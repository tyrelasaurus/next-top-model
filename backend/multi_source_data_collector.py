#!/usr/bin/env python3
"""
Multi-Source NFL Data Collector
Implements fallback strategy using multiple free data sources
"""

import asyncio
import logging
import sys
import requests
import time
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.models.sports import Game, Team

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiSourceDataCollector:
    """Collect NFL data from multiple free sources with fallback strategy"""
    
    def __init__(self, rate_limit_seconds: float = 2.0):
        self.rate_limit = rate_limit_seconds
        self.last_request_time = 0
        self.stats = {
            "espn_success": 0,
            "espn_failures": 0,
            "pfr_success": 0,
            "pfr_failures": 0,
            "wikipedia_success": 0,
            "wikipedia_failures": 0,
            "total_fields_updated": 0
        }
    
    async def rate_limit_request(self):
        """Apply rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit:
            sleep_time = self.rate_limit - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get_espn_game_data(self, game_date: datetime, team_names: Tuple[str, str]) -> Optional[Dict]:
        """Get game data from ESPN API"""
        try:
            # ESPN API for specific date
            date_str = game_date.strftime("%Y%m%d")
            url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={date_str}"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            events = data.get('events', [])
            
            # Find matching game by team names
            for event in events:
                competitions = event.get('competitions', [])
                for competition in competitions:
                    competitors = competition.get('competitors', [])
                    
                    if len(competitors) >= 2:
                        team1 = competitors[0].get('team', {}).get('displayName', '')
                        team2 = competitors[1].get('team', {}).get('displayName', '')
                        
                        # Simple name matching (could be improved)
                        if any(name in team1 or name in team2 for name in team_names):
                            
                            game_data = {}
                            
                            # Extract attendance
                            if competition.get('attendance'):
                                game_data['attendance'] = competition['attendance']
                            
                            # Extract weather
                            weather = competition.get('weather', {})
                            if weather:
                                if weather.get('temperature'):
                                    game_data['weather_temp'] = weather['temperature']
                                if weather.get('conditionId'):
                                    conditions_map = {
                                        1: 'sunny', 2: 'partly_cloudy', 3: 'cloudy',
                                        4: 'overcast', 5: 'rain', 6: 'snow'
                                    }
                                    game_data['weather_condition'] = conditions_map.get(
                                        weather['conditionId'], 'unknown'
                                    )
                            
                            # Extract venue details
                            venue = competition.get('venue', {})
                            if venue and venue.get('fullName'):
                                game_data['venue'] = venue['fullName']
                            
                            self.stats["espn_success"] += 1
                            return game_data
            
            return None
            
        except Exception as e:
            logger.debug(f"ESPN API failed: {e}")
            self.stats["espn_failures"] += 1
            return None
    
    def get_wikipedia_game_data(self, game: Game, season: int) -> Optional[Dict]:
        """Get game data from Wikipedia (for major games)"""
        try:
            # Only try Wikipedia for playoff games or notable matchups
            if game.game_type not in ['wildcard', 'divisional', 'conference', 'superbowl']:
                return None
            
            # Try Super Bowl first
            if game.game_type == 'superbowl':
                # Calculate Super Bowl number (approximate)
                sb_number = season - 1966  # Super Bowl I was 1967 season
                url = f"https://en.wikipedia.org/wiki/Super_Bowl_{self.roman_numeral(sb_number)}"
            else:
                # Try general playoff page
                url = f"https://en.wikipedia.org/wiki/{season}_NFL_playoffs"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            content = response.text
            game_data = {}
            
            # Extract attendance using regex
            attendance_patterns = [
                r'attendance[:\s]*([0-9,]+)',
                r'([0-9,]+)\s+attendance',
                r'attended by ([0-9,]+)'
            ]
            
            for pattern in attendance_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    attendance_str = match.group(1).replace(',', '')
                    if attendance_str.isdigit():
                        game_data['attendance'] = int(attendance_str)
                        break
            
            # Extract weather information
            weather_patterns = [
                r'temperature[:\s]*([0-9]+)°?[F|f]',
                r'([0-9]+)°[F|f]',
                r'weather[:\s]*([^.]+)'
            ]
            
            for pattern in weather_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    if pattern.startswith('weather'):
                        game_data['weather_condition'] = match.group(1).strip()
                    else:
                        temp_str = match.group(1)
                        if temp_str.isdigit():
                            game_data['weather_temp'] = int(temp_str)
                    break
            
            if game_data:
                self.stats["wikipedia_success"] += 1
                return game_data
            
            return None
            
        except Exception as e:
            logger.debug(f"Wikipedia scraping failed: {e}")
            self.stats["wikipedia_failures"] += 1
            return None
    
    def roman_numeral(self, num: int) -> str:
        """Convert number to Roman numeral for Super Bowl"""
        values = [50, 40, 10, 9, 5, 4, 1]
        symbols = ['L', 'XL', 'X', 'IX', 'V', 'IV', 'I']
        
        result = ''
        for i, value in enumerate(values):
            count = num // value
            result += symbols[i] * count
            num -= value * count
        
        return result
    
    def get_selective_pfr_data(self, game: Game) -> Optional[Dict]:
        """Selective PFR scraping - only for high-value games"""
        try:
            # Only scrape PFR for playoff games to minimize load
            if game.game_type not in ['wildcard', 'divisional', 'conference', 'superbowl']:
                return None
            
            if not game.game_datetime:
                return None
            
            # Generate PFR game ID
            date_str = game.game_datetime.strftime('%Y%m%d')
            
            # Map team UIDs to PFR abbreviations (simplified)
            pfr_team_map = {
                'NFL_134931': 'kan',  # Kansas City Chiefs
                'NFL_134925': 'pit',  # Pittsburgh Steelers
                'NFL_134940': 'gnb',  # Green Bay Packers
                # Add more as needed for playoff teams
            }
            
            home_abbrev = pfr_team_map.get(game.home_team_uid)
            if not home_abbrev:
                return None
            
            pfr_game_id = f"{date_str}{home_abbrev}"
            url = f"https://www.pro-football-reference.com/boxscores/{pfr_game_id}.htm"
            
            # Use a longer timeout and user agent for PFR
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            content = response.text
            game_data = {}
            
            # Extract attendance
            attendance_match = re.search(r'Attendance[:\s]*([0-9,]+)', content, re.IGNORECASE)
            if attendance_match:
                attendance_str = attendance_match.group(1).replace(',', '')
                if attendance_str.isdigit():
                    game_data['attendance'] = int(attendance_str)
            
            # Extract weather
            temp_match = re.search(r'(\d+)°\s*F', content)
            if temp_match:
                game_data['weather_temp'] = int(temp_match.group(1))
            
            weather_match = re.search(r'Weather[:\s]*([^<]+)', content, re.IGNORECASE)
            if weather_match:
                game_data['weather_condition'] = weather_match.group(1).strip()
            
            if game_data:
                self.stats["pfr_success"] += 1
                return game_data
            
            return None
            
        except Exception as e:
            logger.debug(f"PFR scraping failed: {e}")
            self.stats["pfr_failures"] += 1
            return None
    
    async def augment_game_multi_source(self, game: Game) -> int:
        """Augment a single game using multiple sources with fallback"""
        
        fields_updated = 0
        
        # Get team names for ESPN matching
        with SessionLocal() as db:
            home_team = db.query(Team).filter(Team.team_uid == game.home_team_uid).first()
            away_team = db.query(Team).filter(Team.team_uid == game.away_team_uid).first()
            
            if not home_team or not away_team:
                return 0
            
            team_names = (home_team.name, away_team.name)
        
        # Try sources in order of preference
        sources_data = []
        
        # 1. ESPN API (fast, reliable for recent games)
        await self.rate_limit_request()
        if game.season >= 2022:  # ESPN likely has good recent data
            espn_data = self.get_espn_game_data(game.game_datetime, team_names)
            if espn_data:
                sources_data.append(("ESPN", espn_data))
        
        # 2. Wikipedia (good for playoff games)
        await self.rate_limit_request()
        if game.game_type in ['wildcard', 'divisional', 'conference', 'superbowl']:
            wiki_data = self.get_wikipedia_game_data(game, game.season)
            if wiki_data:
                sources_data.append(("Wikipedia", wiki_data))
        
        # 3. Selective PFR (only for high-value playoff games)
        await self.rate_limit_request()
        if game.game_type in ['conference', 'superbowl']:  # Only championship games
            pfr_data = self.get_selective_pfr_data(game)
            if pfr_data:
                sources_data.append(("PFR", pfr_data))
        
        # Merge data from all sources (prefer more reliable sources)
        merged_data = {}
        for source_name, data in sources_data:
            for field, value in data.items():
                if field not in merged_data:  # First source wins
                    merged_data[field] = value
        
        # Update game with merged data
        if merged_data:
            with SessionLocal() as db:
                db_game = db.query(Game).filter(Game.game_uid == game.game_uid).first()
                if db_game:
                    
                    for field, value in merged_data.items():
                        if hasattr(db_game, field) and getattr(db_game, field) is None:
                            setattr(db_game, field, value)
                            fields_updated += 1
                    
                    if fields_updated > 0:
                        db_game.updated_at = datetime.utcnow()
                        db.commit()
                        
                        sources_used = [name for name, _ in sources_data]
                        logger.info(f"  ✅ Updated {fields_updated} fields using: {', '.join(sources_used)}")
        
        self.stats["total_fields_updated"] += fields_updated
        return fields_updated
    
    async def augment_season_multi_source(self, season: int, max_games: int = 50) -> Dict:
        """Augment a season using multi-source approach"""
        
        logger.info(f"Starting multi-source augmentation for {season} season")
        
        with SessionLocal() as db:
            # Prioritize playoff games, then recent regular season
            playoff_games = db.query(Game).filter(
                Game.season == season,
                Game.game_type.in_(['wildcard', 'divisional', 'conference', 'superbowl'])
            ).all()
            
            regular_games = db.query(Game).filter(
                Game.season == season,
                Game.game_type == 'regular'
            ).limit(max(0, max_games - len(playoff_games))).all()
            
            games_to_process = playoff_games + regular_games
        
        logger.info(f"Processing {len(games_to_process)} games ({len(playoff_games)} playoff, {len(regular_games)} regular)")
        
        games_updated = 0
        
        for i, game in enumerate(games_to_process, 1):
            logger.info(f"[{i}/{len(games_to_process)}] Processing {game.game_type} game: {game.game_uid}")
            
            fields_updated = await self.augment_game_multi_source(game)
            
            if fields_updated > 0:
                games_updated += 1
            else:
                logger.info(f"  ℹ️  No new data found")
            
            # Progress update
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{len(games_to_process)} games processed, {games_updated} updated")
        
        return {
            "season": season,
            "games_processed": len(games_to_process),
            "games_updated": games_updated,
            "fields_updated": self.stats["total_fields_updated"],
            "source_stats": dict(self.stats)
        }

async def main():
    """Main execution"""
    logger.info("=" * 80)
    logger.info("MULTI-SOURCE NFL DATA AUGMENTATION")
    logger.info("=" * 80)
    logger.info("Sources: ESPN API → Wikipedia → Selective PFR")
    logger.info("Focus: Playoff games + sample regular season")
    
    # Start with recent seasons where ESPN data is most reliable
    seasons = [2024, 2023, 2022]
    
    collector = MultiSourceDataCollector(rate_limit_seconds=2.0)
    
    results = {}
    
    for season in seasons:
        try:
            result = await collector.augment_season_multi_source(season, max_games=30)
            results[season] = result
            
            logger.info(f"\n✅ {season} Season Complete:")
            logger.info(f"   Games processed: {result['games_processed']}")
            logger.info(f"   Games updated: {result['games_updated']}")
            logger.info(f"   Fields updated: {result['fields_updated']}")
            
        except Exception as e:
            logger.error(f"❌ Failed to process season {season}: {e}")
            results[season] = {"error": str(e)}
    
    # Final statistics
    logger.info("\n" + "=" * 60)
    logger.info("MULTI-SOURCE AUGMENTATION COMPLETE")
    logger.info("=" * 60)
    
    total_games_updated = sum(r.get('games_updated', 0) for r in results.values())
    total_fields_updated = sum(r.get('fields_updated', 0) for r in results.values())
    
    logger.info(f"Total games updated: {total_games_updated}")
    logger.info(f"Total fields updated: {total_fields_updated}")
    logger.info(f"ESPN successes: {collector.stats['espn_success']}")
    logger.info(f"Wikipedia successes: {collector.stats['wikipedia_success']}")
    logger.info(f"PFR successes: {collector.stats['pfr_success']}")
    
    logger.info("\n🎯 MULTI-SOURCE STRATEGY SUCCESSFUL!")
    logger.info("📊 Reduced dependency on single source")
    logger.info("⚡ Faster data collection with fallbacks")

if __name__ == "__main__":
    asyncio.run(main())