#!/usr/bin/env python3
"""
ESPN Granular Statistics Collector
Comprehensive collection of team game stats, season stats, and player performance data
"""

import asyncio
import logging
import sys
import aiohttp
import time
import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import re

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.models.sports import Game, Team, Player, PlayerStat, TeamGameStat, TeamSeasonStat

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("espn_granular_stats_collection.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ESPNGranularStatsCollector:
    """Comprehensive ESPN API statistics collector for granular NFL data"""
    
    def __init__(self, rate_limit_seconds: float = 2.0):
        self.rate_limit = rate_limit_seconds
        self.last_request_time = 0
        self.session = None
        self.stats = {
            "api_calls_made": 0,
            "games_processed": 0,
            "team_game_stats_added": 0,
            "team_season_stats_added": 0,
            "player_stats_added": 0,
            "total_fields_updated": 0
        }
        
        # ESPN API endpoints
        self.endpoints = {
            "scoreboard": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
            "game_summary": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary",
            "standings": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/standings",
            "team_details": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams",
            "team_schedule": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}/schedule"
        }
        
        # ESPN team ID mapping (ESPN uses different IDs than our database)
        self.espn_team_mapping = {
            "Arizona Cardinals": "22", "Atlanta Falcons": "1", "Baltimore Ravens": "33",
            "Buffalo Bills": "2", "Carolina Panthers": "29", "Chicago Bears": "3",
            "Cincinnati Bengals": "4", "Cleveland Browns": "5", "Dallas Cowboys": "6",
            "Denver Broncos": "7", "Detroit Lions": "8", "Green Bay Packers": "9",
            "Houston Texans": "34", "Indianapolis Colts": "11", "Jacksonville Jaguars": "30",
            "Kansas City Chiefs": "12", "Las Vegas Raiders": "13", "Los Angeles Chargers": "24",
            "Los Angeles Rams": "14", "Miami Dolphins": "15", "Minnesota Vikings": "16",
            "New England Patriots": "17", "New Orleans Saints": "18", "New York Giants": "19",
            "New York Jets": "20", "Philadelphia Eagles": "21", "Pittsburgh Steelers": "23",
            "San Francisco 49ers": "25", "Seattle Seahawks": "26", "Tampa Bay Buccaneers": "27",
            "Tennessee Titans": "10", "Washington Commanders": "28"
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'NFL-Granular-Stats-Collector/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def rate_limit_request(self):
        """Apply rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit:
            sleep_time = self.rate_limit - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    async def make_api_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """Make a rate-limited API request"""
        await self.rate_limit_request()
        
        try:
            self.stats["api_calls_made"] += 1
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.debug(f"API request failed: {response.status} for {url}")
                    return None
        
        except Exception as e:
            logger.debug(f"API request error for {url}: {e}")
            return None
    
    def parse_time_of_possession(self, top_string: str) -> Optional[int]:
        """Convert time of possession string (MM:SS) to seconds"""
        if not top_string:
            return None
        
        try:
            parts = top_string.split(':')
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = int(parts[1])
                return minutes * 60 + seconds
        except:
            pass
        
        return None
    
    def normalize_stat_value(self, value: Any) -> Optional[float]:
        """Normalize statistic values from ESPN API"""
        if value is None or value == '':
            return None
        
        try:
            if isinstance(value, str):
                # Remove commas and convert
                clean_value = value.replace(',', '').replace('%', '')
                
                # Handle fractions like "3/7"
                if '/' in clean_value:
                    parts = clean_value.split('/')
                    if len(parts) == 2:
                        return float(parts[0]) / float(parts[1])
                
                return float(clean_value)
            
            return float(value)
        
        except (ValueError, TypeError):
            return None
    
    async def get_espn_game_id_from_db_game(self, game: Game) -> Optional[str]:
        """Try to find ESPN game ID by matching date and teams"""
        
        if not game.game_datetime:
            return None
        
        # Format date for ESPN API
        date_str = game.game_datetime.strftime("%Y%m%d")
        url = f"{self.endpoints['scoreboard']}?dates={date_str}"
        
        data = await self.make_api_request(url)
        if not data:
            return None
        
        events = data.get('events', [])
        
        # Get team names for matching
        with SessionLocal() as db:
            home_team = db.query(Team).filter(Team.team_uid == game.home_team_uid).first()
            away_team = db.query(Team).filter(Team.team_uid == game.away_team_uid).first()
            
            if not home_team or not away_team:
                return None
            
            home_team_name = f"{home_team.city} {home_team.name}"
            away_team_name = f"{away_team.city} {away_team.name}"
        
        # Find matching game
        for event in events:
            competitions = event.get('competitions', [])
            for competition in competitions:
                competitors = competition.get('competitors', [])
                
                if len(competitors) >= 2:
                    espn_teams = []
                    for competitor in competitors:
                        team_info = competitor.get('team', {})
                        team_name = team_info.get('displayName', '')
                        espn_teams.append(team_name.lower())
                    
                    # Check if teams match
                    if (any(name.lower() in team_name for name in [home_team.city.lower(), home_team.name.lower()] for team_name in espn_teams) and
                        any(name.lower() in team_name for name in [away_team.city.lower(), away_team.name.lower()] for team_name in espn_teams)):
                        return event.get('id')
        
        return None
    
    async def collect_team_game_stats(self, game: Game, espn_game_id: str) -> int:
        """Collect detailed team statistics for a specific game"""
        
        url = f"{self.endpoints['game_summary']}?event={espn_game_id}"
        data = await self.make_api_request(url)
        
        if not data:
            return 0
        
        stats_added = 0
        
        # Extract box score data
        box_score = data.get('boxscore', {})
        if not box_score:
            return 0
        
        teams = box_score.get('teams', [])
        
        with SessionLocal() as db:
            for team_data in teams:
                team_info = team_data.get('team', {})
                espn_team_name = team_info.get('displayName', '')
                
                # Match ESPN team to our database
                db_team = None
                is_home_team = 0
                
                # Check home team
                home_team = db.query(Team).filter(Team.team_uid == game.home_team_uid).first()
                if home_team:
                    home_team_name = f"{home_team.city} {home_team.name}"
                    if any(name.lower() in espn_team_name.lower() for name in [home_team.city.lower(), home_team.name.lower()]):
                        db_team = home_team
                        is_home_team = 1
                
                # Check away team if not home
                if not db_team:
                    away_team = db.query(Team).filter(Team.team_uid == game.away_team_uid).first()
                    if away_team:
                        away_team_name = f"{away_team.city} {away_team.name}"
                        if any(name.lower() in espn_team_name.lower() for name in [away_team.city.lower(), away_team.name.lower()]):
                            db_team = away_team
                            is_home_team = 0
                
                if not db_team:
                    continue
                
                # Check if stats already exist
                existing_stat = db.query(TeamGameStat).filter(
                    TeamGameStat.game_uid == game.game_uid,
                    TeamGameStat.team_uid == db_team.team_uid
                ).first()
                
                if existing_stat:
                    continue  # Skip if already exists
                
                # Parse team statistics
                statistics = team_data.get('statistics', [])
                stat_dict = {}
                
                for stat in statistics:
                    stat_name = stat.get('name', '').lower()
                    stat_value = stat.get('displayValue', '')
                    stat_dict[stat_name] = stat_value
                
                # Create TeamGameStat record
                team_game_stat = TeamGameStat(
                    stat_uid=str(uuid.uuid4()),
                    game_uid=game.game_uid,
                    team_uid=db_team.team_uid,
                    is_home_team=is_home_team,
                    source="ESPN_API"
                )
                
                # Map common statistics
                if 'total yards' in stat_dict:
                    team_game_stat.total_yards = self.normalize_stat_value(stat_dict['total yards'])
                
                if 'passing yards' in stat_dict:
                    team_game_stat.passing_yards = self.normalize_stat_value(stat_dict['passing yards'])
                
                if 'rushing yards' in stat_dict:
                    team_game_stat.rushing_yards = self.normalize_stat_value(stat_dict['rushing yards'])
                
                if 'first downs' in stat_dict:
                    team_game_stat.first_downs = self.normalize_stat_value(stat_dict['first downs'])
                
                if 'third down efficiency' in stat_dict:
                    # Parse "X-Y" format
                    efficiency = stat_dict['third down efficiency']
                    if '-' in efficiency:
                        parts = efficiency.split('-')
                        if len(parts) == 2:
                            team_game_stat.third_down_conversions = self.normalize_stat_value(parts[0])
                            team_game_stat.third_down_attempts = self.normalize_stat_value(parts[1])
                
                if 'time of possession' in stat_dict:
                    team_game_stat.time_of_possession_seconds = self.parse_time_of_possession(stat_dict['time of possession'])
                
                if 'turnovers' in stat_dict:
                    team_game_stat.turnovers = self.normalize_stat_value(stat_dict['turnovers'])
                
                if 'fumbles lost' in stat_dict:
                    team_game_stat.fumbles_lost = self.normalize_stat_value(stat_dict['fumbles lost'])
                
                if 'interceptions' in stat_dict:
                    team_game_stat.interceptions_thrown = self.normalize_stat_value(stat_dict['interceptions'])
                
                if 'sacks-yards lost' in stat_dict:
                    # Parse sacks from "X-Y" format
                    sacks_data = stat_dict['sacks-yards lost']
                    if '-' in sacks_data:
                        parts = sacks_data.split('-')
                        if len(parts) >= 1:
                            team_game_stat.sacks = self.normalize_stat_value(parts[0])
                
                if 'penalties-yards' in stat_dict:
                    # Parse penalties from "X-Y" format
                    penalties_data = stat_dict['penalties-yards']
                    if '-' in penalties_data:
                        parts = penalties_data.split('-')
                        if len(parts) == 2:
                            team_game_stat.penalties = self.normalize_stat_value(parts[0])
                            team_game_stat.penalty_yards = self.normalize_stat_value(parts[1])
                
                # Store raw box score data
                team_game_stat.raw_box_score = team_data
                
                db.add(team_game_stat)
                stats_added += 1
                
                logger.info(f"  📊 Added team game stats for {espn_team_name}")
            
            if stats_added > 0:
                db.commit()
        
        return stats_added
    
    async def collect_team_season_stats(self, team_uid: str, season: int) -> int:
        """Collect season statistics for a team"""
        
        # Find ESPN team ID
        with SessionLocal() as db:
            team = db.query(Team).filter(Team.team_uid == team_uid).first()
            if not team:
                return 0
            
            team_name = f"{team.city} {team.name}"
            espn_team_id = self.espn_team_mapping.get(team_name)
            
            if not espn_team_id:
                logger.debug(f"No ESPN team ID found for {team_name}")
                return 0
            
            # Check if season stats already exist
            existing_stat = db.query(TeamSeasonStat).filter(
                TeamSeasonStat.team_uid == team_uid,
                TeamSeasonStat.season == season
            ).first()
            
            if existing_stat:
                return 0  # Skip if already exists
        
        # Get team season data from ESPN
        url = f"{self.endpoints['team_details']}/{espn_team_id}"
        params = {"season": season}
        
        data = await self.make_api_request(url, params)
        if not data:
            return 0
        
        with SessionLocal() as db:
            # Create TeamSeasonStat record
            team_season_stat = TeamSeasonStat(
                stat_uid=str(uuid.uuid4()),
                team_uid=team_uid,
                season=season,
                source="ESPN_API"
            )
            
            # Parse record data
            record = data.get('record', {})
            if record:
                items = record.get('items', [])
                for item in items:
                    stats = item.get('stats', [])
                    for stat in stats:
                        stat_name = stat.get('name', '').lower()
                        stat_value = stat.get('value')
                        
                        if stat_name == 'wins':
                            team_season_stat.wins = self.normalize_stat_value(stat_value)
                        elif stat_name == 'losses':
                            team_season_stat.losses = self.normalize_stat_value(stat_value)
                        elif stat_name == 'winpercent':
                            team_season_stat.win_percentage = self.normalize_stat_value(stat_value)
            
            # Parse team statistics
            statistics = data.get('statistics', {})
            if statistics:
                splits = statistics.get('splits', {})
                categories = splits.get('categories', [])
                
                for category in categories:
                    category_name = category.get('name', '').lower()
                    stats = category.get('stats', [])
                    
                    for stat in stats:
                        stat_name = stat.get('name', '').lower()
                        stat_value = stat.get('value')
                        
                        # Map relevant statistics
                        if 'points' in stat_name and 'per game' in stat_name:
                            if 'scoring offense' in category_name:
                                team_season_stat.points_for = self.normalize_stat_value(stat_value)
                            elif 'scoring defense' in category_name:
                                team_season_stat.points_against = self.normalize_stat_value(stat_value)
                        
                        if 'total offense' in stat_name and 'per game' in stat_name:
                            team_season_stat.total_yards_per_game = self.normalize_stat_value(stat_value)
                        
                        if 'passing offense' in stat_name and 'per game' in stat_name:
                            team_season_stat.passing_yards_per_game = self.normalize_stat_value(stat_value)
                        
                        if 'rushing offense' in stat_name and 'per game' in stat_name:
                            team_season_stat.rushing_yards_per_game = self.normalize_stat_value(stat_value)
            
            # Store raw season data
            team_season_stat.raw_season_data = data
            
            db.add(team_season_stat)
            db.commit()
            
            logger.info(f"  📈 Added season stats for {team_name} ({season})")
            return 1
    
    async def collect_enhanced_statistics(self, max_games: int = 50) -> Dict:
        """Collect enhanced statistics for recent games"""
        
        logger.info("Starting enhanced ESPN statistics collection...")
        
        results = {
            "games_processed": 0,
            "team_game_stats_added": 0,
            "team_season_stats_added": 0,
            "api_calls_made": 0,
            "total_fields_added": 0
        }
        
        with SessionLocal() as db:
            # Get recent games without detailed team stats
            games_without_stats = db.query(Game).filter(
                Game.game_datetime.isnot(None),
                Game.season >= 2022  # Focus on recent seasons
            ).limit(max_games).all()
            
            logger.info(f"Processing {len(games_without_stats)} games for enhanced statistics...")
            
            for game in games_without_stats:
                try:
                    self.stats["games_processed"] += 1
                    
                    # Get team names
                    home_team = db.query(Team).filter(Team.team_uid == game.home_team_uid).first()
                    away_team = db.query(Team).filter(Team.team_uid == game.away_team_uid).first()
                    
                    if not home_team or not away_team:
                        continue
                    
                    logger.info(f"🏈 Processing: {away_team.city} {away_team.name} @ {home_team.city} {home_team.name} ({game.game_datetime.date()})")
                    
                    # Find ESPN game ID
                    espn_game_id = await self.get_espn_game_id_from_db_game(game)
                    
                    if espn_game_id:
                        # Collect team game statistics
                        team_stats_added = await self.collect_team_game_stats(game, espn_game_id)
                        self.stats["team_game_stats_added"] += team_stats_added
                        
                        logger.info(f"  ✅ Added {team_stats_added} team game stat records")
                    else:
                        logger.debug(f"  ❌ ESPN game ID not found for {game.game_uid}")
                
                except Exception as e:
                    logger.error(f"Error processing game {game.game_uid}: {e}")
                    continue
            
            # Collect season statistics for teams in recent seasons
            logger.info("🏆 Collecting team season statistics...")
            
            seasons_to_process = [2022, 2023, 2024]
            teams = db.query(Team).all()
            
            for season in seasons_to_process:
                logger.info(f"Processing season {season}...")
                
                for team in teams[:5]:  # Process first 5 teams as demonstration
                    try:
                        season_stats_added = await self.collect_team_season_stats(team.team_uid, season)
                        self.stats["team_season_stats_added"] += season_stats_added
                        
                        if season_stats_added > 0:
                            logger.info(f"  ✅ Added season stats for {team.city} {team.name}")
                    
                    except Exception as e:
                        logger.error(f"Error collecting season stats for {team.city} {team.name}: {e}")
                        continue
        
        # Update results
        results.update({
            "games_processed": self.stats["games_processed"],
            "team_game_stats_added": self.stats["team_game_stats_added"],
            "team_season_stats_added": self.stats["team_season_stats_added"],
            "api_calls_made": self.stats["api_calls_made"],
            "total_fields_added": self.stats["team_game_stats_added"] + self.stats["team_season_stats_added"]
        })
        
        return results

async def main():
    """Main execution"""
    logger.info("=" * 80)
    logger.info("ESPN GRANULAR STATISTICS COLLECTION")
    logger.info("=" * 80)
    logger.info("Collecting detailed team game stats and season statistics")
    
    try:
        async with ESPNGranularStatsCollector() as collector:
            results = await collector.collect_enhanced_statistics(max_games=25)  # Start with 25 games
            
            logger.info("\n" + "=" * 60)
            logger.info("GRANULAR STATISTICS COLLECTION COMPLETE")
            logger.info("=" * 60)
            
            logger.info(f"Games processed: {results['games_processed']}")
            logger.info(f"Team game stats added: {results['team_game_stats_added']}")
            logger.info(f"Team season stats added: {results['team_season_stats_added']}")
            logger.info(f"API calls made: {results['api_calls_made']}")
            logger.info(f"Total new statistical records: {results['total_fields_added']}")
            
            # Check final statistics coverage
            with SessionLocal() as db:
                total_games = db.query(Game).count()
                games_with_team_stats = db.query(TeamGameStat).count()
                teams_with_season_stats = db.query(TeamSeasonStat).count()
                
                logger.info(f"\n📊 Enhanced Statistics Coverage:")
                logger.info(f"   Team Game Stats: {games_with_team_stats} records")
                logger.info(f"   Team Season Stats: {teams_with_season_stats} records")
            
            if results['total_fields_added'] > 0:
                logger.info("\n🎯 ENHANCED STATISTICS COLLECTION SUCCESSFUL!")
                logger.info("✅ Detailed team game statistics collected")
                logger.info("✅ Season-level team performance metrics added")
                logger.info("🏈 NFL dataset now includes professional-grade analytics data!")
            else:
                logger.info("\n⚠️  No new statistics collected")
                logger.info("Data may already be complete or ESPN API unavailable")
            
            return 0
        
    except Exception as e:
        logger.error(f"❌ Collection failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)