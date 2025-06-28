#!/usr/bin/env python3
"""
ESPN Overnight Statistics Collector
Optimized for long-running collection with resume capability
Designed to run overnight and handle timeouts gracefully
"""

import asyncio
import logging
import sys
import aiohttp
import time
import json
import uuid
import pickle
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
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
        logging.FileHandler("espn_overnight_collection.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OvernightStatsCollector:
    """Optimized collector for overnight execution with resume capability"""
    
    def __init__(self, rate_limit_seconds: float = 1.5):
        self.rate_limit = rate_limit_seconds  # Slightly faster while still respectful
        self.last_request_time = 0
        self.session = None
        self.progress_file = "espn_collection_progress.pkl"
        
        # Statistics tracking
        self.stats = {
            "total_api_calls": 0,
            "games_processed": 0,
            "games_skipped": 0,
            "team_game_stats_added": 0,
            "team_season_stats_added": 0,
            "errors_encountered": 0,
            "start_time": None,
            "last_save_time": None
        }
        
        # Progress tracking
        self.processed_games: Set[str] = set()
        self.processed_team_seasons: Set[str] = set()
        self.failed_games: Set[str] = set()
        
        # ESPN API endpoints
        self.endpoints = {
            "scoreboard": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
            "game_summary": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary",
            "team_details": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams"
        }
        
        # ESPN team ID mapping
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
    
    def save_progress(self):
        """Save current progress to file"""
        progress_data = {
            "processed_games": self.processed_games,
            "processed_team_seasons": self.processed_team_seasons,
            "failed_games": self.failed_games,
            "stats": self.stats
        }
        
        try:
            with open(self.progress_file, 'wb') as f:
                pickle.dump(progress_data, f)
            self.stats["last_save_time"] = datetime.now()
            logger.info(f"Progress saved: {len(self.processed_games)} games, {len(self.processed_team_seasons)} team seasons")
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")
    
    def load_progress(self):
        """Load previous progress from file"""
        try:
            if Path(self.progress_file).exists():
                with open(self.progress_file, 'rb') as f:
                    progress_data = pickle.load(f)
                
                self.processed_games = progress_data.get("processed_games", set())
                self.processed_team_seasons = progress_data.get("processed_team_seasons", set())
                self.failed_games = progress_data.get("failed_games", set())
                
                # Restore some stats but reset counters for this session
                previous_stats = progress_data.get("stats", {})
                logger.info(f"Resuming from previous session:")
                logger.info(f"  Previously processed: {len(self.processed_games)} games")
                logger.info(f"  Previously processed: {len(self.processed_team_seasons)} team seasons")
                logger.info(f"  Previously failed: {len(self.failed_games)} games")
                
        except Exception as e:
            logger.warning(f"Could not load previous progress: {e}")
            logger.info("Starting fresh collection")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=45),  # Longer timeout
            headers={'User-Agent': 'NFL-Overnight-Collector/1.0'},
            connector=aiohttp.TCPConnector(limit=10)  # Connection pooling
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def rate_limit_request(self):
        """Apply optimized rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit:
            sleep_time = self.rate_limit - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    async def make_api_request(self, url: str, params: Dict = None, retries: int = 3) -> Optional[Dict]:
        """Make a rate-limited API request with retry logic"""
        await self.rate_limit_request()
        
        for attempt in range(retries):
            try:
                self.stats["total_api_calls"] += 1
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    elif response.status == 429:  # Rate limited
                        logger.warning(f"Rate limited, waiting longer...")
                        await asyncio.sleep(5)
                        continue
                    else:
                        logger.debug(f"API request failed: {response.status} for {url}")
                        if attempt < retries - 1:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                            continue
                        return None
            
            except asyncio.TimeoutError:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{retries})")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return None
            except Exception as e:
                logger.debug(f"API request error for {url}: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return None
        
        return None
    
    def normalize_stat_value(self, value: Any) -> Optional[float]:
        """Normalize statistic values from ESPN API"""
        if value is None or value == '':
            return None
        
        try:
            if isinstance(value, str):
                clean_value = value.replace(',', '').replace('%', '')
                if '/' in clean_value:
                    parts = clean_value.split('/')
                    if len(parts) == 2 and parts[1] != '0':
                        return float(parts[0]) / float(parts[1])
                return float(clean_value)
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def parse_time_of_possession(self, top_string: str) -> Optional[int]:
        """Convert time of possession string (MM:SS) to seconds"""
        if not top_string:
            return None
        try:
            parts = top_string.split(':')
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
        except:
            pass
        return None
    
    async def find_espn_game_id(self, game: Game) -> Optional[str]:
        """Find ESPN game ID by matching date and teams"""
        if not game.game_datetime or game.game_uid in self.failed_games:
            return None
        
        date_str = game.game_datetime.strftime("%Y%m%d")
        url = f"{self.endpoints['scoreboard']}?dates={date_str}"
        
        data = await self.make_api_request(url)
        if not data:
            return None
        
        # Get team names for matching
        with SessionLocal() as db:
            home_team = db.query(Team).filter(Team.team_uid == game.home_team_uid).first()
            away_team = db.query(Team).filter(Team.team_uid == game.away_team_uid).first()
            
            if not home_team or not away_team:
                return None
            
            home_names = [home_team.city.lower(), home_team.name.lower(), 
                         f"{home_team.city} {home_team.name}".lower()]
            away_names = [away_team.city.lower(), away_team.name.lower(),
                         f"{away_team.city} {away_team.name}".lower()]
        
        # Find matching game
        events = data.get('events', [])
        for event in events:
            competitions = event.get('competitions', [])
            for competition in competitions:
                competitors = competition.get('competitors', [])
                
                if len(competitors) >= 2:
                    espn_team_names = []
                    for competitor in competitors:
                        team_info = competitor.get('team', {})
                        team_name = team_info.get('displayName', '').lower()
                        espn_team_names.append(team_name)
                    
                    # Check for matches
                    home_match = any(any(name in espn_name for name in home_names) for espn_name in espn_team_names)
                    away_match = any(any(name in espn_name for name in away_names) for espn_name in espn_team_names)
                    
                    if home_match and away_match:
                        return event.get('id')
        
        return None
    
    async def collect_team_game_stats(self, game: Game, espn_game_id: str) -> int:
        """Collect team game statistics with enhanced parsing"""
        url = f"{self.endpoints['game_summary']}?event={espn_game_id}"
        data = await self.make_api_request(url)
        
        if not data:
            return 0
        
        box_score = data.get('boxscore', {})
        if not box_score:
            return 0
        
        teams = box_score.get('teams', [])
        stats_added = 0
        
        with SessionLocal() as db:
            for team_data in teams:
                team_info = team_data.get('team', {})
                espn_team_name = team_info.get('displayName', '').lower()
                
                # Match to database team
                db_team = None
                is_home_team = 0
                
                home_team = db.query(Team).filter(Team.team_uid == game.home_team_uid).first()
                away_team = db.query(Team).filter(Team.team_uid == game.away_team_uid).first()
                
                if home_team:
                    home_names = [home_team.city.lower(), home_team.name.lower()]
                    if any(name in espn_team_name for name in home_names):
                        db_team = home_team
                        is_home_team = 1
                
                if not db_team and away_team:
                    away_names = [away_team.city.lower(), away_team.name.lower()]
                    if any(name in espn_team_name for name in away_names):
                        db_team = away_team
                        is_home_team = 0
                
                if not db_team:
                    continue
                
                # Check if already exists
                existing = db.query(TeamGameStat).filter(
                    TeamGameStat.game_uid == game.game_uid,
                    TeamGameStat.team_uid == db_team.team_uid
                ).first()
                
                if existing:
                    continue
                
                # Parse statistics
                statistics = team_data.get('statistics', [])
                stat_dict = {stat.get('name', '').lower(): stat.get('displayValue', '') 
                           for stat in statistics}
                
                # Create record
                team_stat = TeamGameStat(
                    stat_uid=str(uuid.uuid4()),
                    game_uid=game.game_uid,
                    team_uid=db_team.team_uid,
                    is_home_team=is_home_team,
                    source="ESPN_API"
                )
                
                # Parse key statistics
                team_stat.total_yards = self.normalize_stat_value(stat_dict.get('total yards'))
                team_stat.passing_yards = self.normalize_stat_value(stat_dict.get('passing yards'))
                team_stat.rushing_yards = self.normalize_stat_value(stat_dict.get('rushing yards'))
                team_stat.first_downs = self.normalize_stat_value(stat_dict.get('first downs'))
                team_stat.turnovers = self.normalize_stat_value(stat_dict.get('turnovers'))
                
                # Parse third down efficiency (format: "X-Y")
                third_down = stat_dict.get('third down efficiency', '')
                if '-' in third_down:
                    parts = third_down.split('-')
                    if len(parts) == 2:
                        team_stat.third_down_conversions = self.normalize_stat_value(parts[0])
                        team_stat.third_down_attempts = self.normalize_stat_value(parts[1])
                
                # Parse time of possession
                top = stat_dict.get('time of possession', '')
                team_stat.time_of_possession_seconds = self.parse_time_of_possession(top)
                
                # Parse penalties (format: "X-Y")
                penalties = stat_dict.get('penalties-yards', '')
                if '-' in penalties:
                    parts = penalties.split('-')
                    if len(parts) == 2:
                        team_stat.penalties = self.normalize_stat_value(parts[0])
                        team_stat.penalty_yards = self.normalize_stat_value(parts[1])
                
                # Store raw data
                team_stat.raw_box_score = team_data
                
                db.add(team_stat)
                stats_added += 1
            
            if stats_added > 0:
                db.commit()
        
        return stats_added
    
    async def collect_team_season_stats(self, team_uid: str, season: int) -> bool:
        """Collect season statistics for a team"""
        season_key = f"{team_uid}_{season}"
        if season_key in self.processed_team_seasons:
            return False
        
        with SessionLocal() as db:
            team = db.query(Team).filter(Team.team_uid == team_uid).first()
            if not team:
                return False
            
            team_name = f"{team.city} {team.name}"
            espn_team_id = self.espn_team_mapping.get(team_name)
            
            if not espn_team_id:
                self.processed_team_seasons.add(season_key)
                return False
            
            # Check if already exists
            existing = db.query(TeamSeasonStat).filter(
                TeamSeasonStat.team_uid == team_uid,
                TeamSeasonStat.season == season
            ).first()
            
            if existing:
                self.processed_team_seasons.add(season_key)
                return False
        
        # Get ESPN data
        url = f"{self.endpoints['team_details']}/{espn_team_id}"
        params = {"season": season}
        data = await self.make_api_request(url, params)
        
        if not data:
            return False
        
        with SessionLocal() as db:
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
                        name = stat.get('name', '').lower()
                        value = stat.get('value')
                        
                        if name == 'wins':
                            team_season_stat.wins = self.normalize_stat_value(value)
                        elif name == 'losses':
                            team_season_stat.losses = self.normalize_stat_value(value)
                        elif name == 'winpercent':
                            team_season_stat.win_percentage = self.normalize_stat_value(value)
            
            # Calculate point differential if we have both
            if team_season_stat.points_for and team_season_stat.points_against:
                team_season_stat.points_differential = team_season_stat.points_for - team_season_stat.points_against
            
            team_season_stat.raw_season_data = data
            
            db.add(team_season_stat)
            db.commit()
            
            self.processed_team_seasons.add(season_key)
            return True
    
    async def run_overnight_collection(self):
        """Main overnight collection process"""
        self.stats["start_time"] = datetime.now()
        logger.info("=" * 80)
        logger.info("ESPN OVERNIGHT STATISTICS COLLECTION STARTED")
        logger.info("=" * 80)
        
        # Load previous progress
        self.load_progress()
        
        with SessionLocal() as db:
            # Get all games, prioritizing recent seasons
            all_games = db.query(Game).filter(
                Game.game_datetime.isnot(None),
                Game.season >= 2022  # Focus on 2022+ for better ESPN availability
            ).order_by(Game.season.desc(), Game.game_datetime.desc()).all()
            
            total_games = len(all_games)
            logger.info(f"Total games to process: {total_games}")
            logger.info(f"Already processed: {len(self.processed_games)}")
            logger.info(f"Remaining: {total_games - len(self.processed_games)}")
        
        # Process games
        for i, game in enumerate(all_games):
            if game.game_uid in self.processed_games:
                self.stats["games_skipped"] += 1
                continue
            
            try:
                # Progress logging
                if i % 50 == 0:
                    elapsed = datetime.now() - self.stats["start_time"]
                    rate = self.stats["games_processed"] / elapsed.total_seconds() * 60 if elapsed.total_seconds() > 0 else 0
                    logger.info(f"Progress: {i}/{total_games} games ({i/total_games*100:.1f}%) - Rate: {rate:.1f} games/min")
                
                with SessionLocal() as db:
                    home_team = db.query(Team).filter(Team.team_uid == game.home_team_uid).first()
                    away_team = db.query(Team).filter(Team.team_uid == game.away_team_uid).first()
                    
                    if not home_team or not away_team:
                        self.processed_games.add(game.game_uid)
                        continue
                
                # Find ESPN game ID
                espn_game_id = await self.find_espn_game_id(game)
                
                if espn_game_id:
                    # Collect team game stats
                    stats_added = await self.collect_team_game_stats(game, espn_game_id)
                    self.stats["team_game_stats_added"] += stats_added
                    
                    if stats_added > 0:
                        logger.info(f"✅ {away_team.city} {away_team.name} @ {home_team.city} {home_team.name} ({game.game_datetime.date()}) - {stats_added} stats")
                else:
                    self.failed_games.add(game.game_uid)
                
                self.processed_games.add(game.game_uid)
                self.stats["games_processed"] += 1
                
                # Save progress every 25 games
                if self.stats["games_processed"] % 25 == 0:
                    self.save_progress()
            
            except Exception as e:
                self.stats["errors_encountered"] += 1
                logger.error(f"Error processing game {game.game_uid}: {e}")
                self.failed_games.add(game.game_uid)
                continue
        
        # Collect season statistics
        logger.info("🏆 Starting team season statistics collection...")
        
        with SessionLocal() as db:
            teams = db.query(Team).all()
            seasons = [2022, 2023, 2024]
            
            for season in seasons:
                logger.info(f"Processing season {season}...")
                for team in teams:
                    try:
                        success = await self.collect_team_season_stats(team.team_uid, season)
                        if success:
                            self.stats["team_season_stats_added"] += 1
                            logger.info(f"✅ {team.city} {team.name} ({season})")
                    except Exception as e:
                        logger.error(f"Error collecting season stats for {team.city} {team.name}: {e}")
                        continue
        
        # Final save
        self.save_progress()
        
        # Summary
        elapsed = datetime.now() - self.stats["start_time"]
        logger.info("\n" + "=" * 60)
        logger.info("OVERNIGHT COLLECTION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total runtime: {elapsed}")
        logger.info(f"Games processed: {self.stats['games_processed']}")
        logger.info(f"Games skipped: {self.stats['games_skipped']}")
        logger.info(f"Team game stats added: {self.stats['team_game_stats_added']}")
        logger.info(f"Team season stats added: {self.stats['team_season_stats_added']}")
        logger.info(f"API calls made: {self.stats['total_api_calls']}")
        logger.info(f"Errors encountered: {self.stats['errors_encountered']}")
        
        # Final database check
        with SessionLocal() as db:
            total_team_game_stats = db.query(TeamGameStat).count()
            total_team_season_stats = db.query(TeamSeasonStat).count()
            
            logger.info(f"\n📊 Final Database Statistics:")
            logger.info(f"   Team Game Stats: {total_team_game_stats} records")
            logger.info(f"   Team Season Stats: {total_team_season_stats} records")
        
        logger.info("\n🎯 COLLECTION SUCCESSFULLY COMPLETED!")

async def main():
    """Main execution function"""
    try:
        async with OvernightStatsCollector() as collector:
            await collector.run_overnight_collection()
        return 0
    except Exception as e:
        logger.error(f"❌ Collection failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)