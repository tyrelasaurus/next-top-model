#!/usr/bin/env python3
"""
Enhanced ESPN API Collector
Based on Public-ESPN-API documentation to improve historical data collection
Focus on weather data and attendance verification for 2021-2024 games
"""

import asyncio
import logging
import sys
import aiohttp
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import re

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.models.sports import Game, Team

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("espn_api_enhanced_collection.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ESPNAPICollector:
    """Enhanced ESPN API collector using Public-ESPN-API documentation"""
    
    def __init__(self, rate_limit_seconds: float = 2.0):
        self.rate_limit = rate_limit_seconds
        self.last_request_time = 0
        self.session = None
        self.stats = {
            "api_calls_made": 0,
            "games_found": 0,
            "weather_data_added": 0,
            "attendance_verified": 0,
            "venue_data_added": 0,
            "total_fields_updated": 0
        }
        
        # ESPN API base URLs from Public-ESPN-API documentation
        self.base_urls = {
            "scoreboard": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
            "schedule": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}/schedule",
            "game_details": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary"
        }
        
        # Team name mappings for better matching
        self.team_name_mappings = {
            "Cardinals": ["Arizona Cardinals", "Arizona", "ARI"],
            "Falcons": ["Atlanta Falcons", "Atlanta", "ATL"],
            "Ravens": ["Baltimore Ravens", "Baltimore", "BAL"],
            "Bills": ["Buffalo Bills", "Buffalo", "BUF"],
            "Panthers": ["Carolina Panthers", "Carolina", "CAR"],
            "Bears": ["Chicago Bears", "Chicago", "CHI"],
            "Bengals": ["Cincinnati Bengals", "Cincinnati", "CIN"],
            "Browns": ["Cleveland Browns", "Cleveland", "CLE"],
            "Cowboys": ["Dallas Cowboys", "Dallas", "DAL"],
            "Broncos": ["Denver Broncos", "Denver", "DEN"],
            "Lions": ["Detroit Lions", "Detroit", "DET"],
            "Packers": ["Green Bay Packers", "Green Bay", "GB"],
            "Texans": ["Houston Texans", "Houston", "HOU"],
            "Colts": ["Indianapolis Colts", "Indianapolis", "IND"],
            "Jaguars": ["Jacksonville Jaguars", "Jacksonville", "JAX"],
            "Chiefs": ["Kansas City Chiefs", "Kansas City", "KC"],
            "Raiders": ["Las Vegas Raiders", "Las Vegas", "LV", "Oakland Raiders"],
            "Chargers": ["Los Angeles Chargers", "LA Chargers", "LAC", "San Diego Chargers"],
            "Rams": ["Los Angeles Rams", "LA Rams", "LAR", "St. Louis Rams"],
            "Dolphins": ["Miami Dolphins", "Miami", "MIA"],
            "Vikings": ["Minnesota Vikings", "Minnesota", "MIN"],
            "Patriots": ["New England Patriots", "New England", "NE"],
            "Saints": ["New Orleans Saints", "New Orleans", "NO"],
            "Giants": ["New York Giants", "NY Giants", "NYG"],
            "Jets": ["New York Jets", "NY Jets", "NYJ"],
            "Eagles": ["Philadelphia Eagles", "Philadelphia", "PHI"],
            "Steelers": ["Pittsburgh Steelers", "Pittsburgh", "PIT"],
            "49ers": ["San Francisco 49ers", "San Francisco", "SF"],
            "Seahawks": ["Seattle Seahawks", "Seattle", "SEA"],
            "Buccaneers": ["Tampa Bay Buccaneers", "Tampa Bay", "TB"],
            "Titans": ["Tennessee Titans", "Tennessee", "TEN"],
            "Commanders": ["Washington Commanders", "Washington", "WAS", "Washington Football Team", "Washington Redskins"]
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'NFL-Data-Collector/1.0'}
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
    
    def match_teams(self, db_home_team: str, db_away_team: str, espn_teams: List[str]) -> bool:
        """Check if ESPN teams match database teams"""
        
        # Create normalized team names for comparison
        db_teams_normalized = []
        for team_name in [db_home_team, db_away_team]:
            # Try to find team in mappings
            for key, mappings in self.team_name_mappings.items():
                if any(name.lower() in team_name.lower() for name in mappings):
                    db_teams_normalized.extend([name.lower() for name in mappings])
                    break
            else:
                # Add original name parts if not found in mappings
                db_teams_normalized.extend([part.lower() for part in team_name.split()])
        
        # Check if ESPN teams match any of our normalized names
        espn_teams_lower = [team.lower() for team in espn_teams]
        
        matches = 0
        for espn_team in espn_teams_lower:
            if any(db_name in espn_team or espn_team in db_name for db_name in db_teams_normalized):
                matches += 1
        
        return matches >= 2  # Both teams should match
    
    async def get_game_data_by_date(self, game_date: datetime, home_team: str, away_team: str) -> Optional[Dict]:
        """Get game data for a specific date"""
        
        # Format date for ESPN API (YYYYMMDD)
        date_str = game_date.strftime("%Y%m%d")
        url = f"{self.base_urls['scoreboard']}?dates={date_str}"
        
        data = await self.make_api_request(url)
        if not data:
            return None
        
        events = data.get('events', [])
        
        # Look for matching game
        for event in events:
            competitions = event.get('competitions', [])
            for competition in competitions:
                competitors = competition.get('competitors', [])
                
                if len(competitors) >= 2:
                    espn_teams = []
                    for competitor in competitors:
                        team_info = competitor.get('team', {})
                        team_name = team_info.get('displayName', '')
                        espn_teams.append(team_name)
                    
                    # Check if this matches our game
                    if self.match_teams(home_team, away_team, espn_teams):
                        logger.info(f"  ✅ Found match: {' vs '.join(espn_teams)}")
                        return competition
        
        return None
    
    async def collect_missing_weather_data(self) -> int:
        """Collect weather data for games that don't have it"""
        
        logger.info("Collecting missing weather data from ESPN API...")
        
        fields_updated = 0
        
        with SessionLocal() as db:
            # Get games without weather data
            games_without_weather = db.query(Game).filter(
                Game.weather_condition.is_(None),
                Game.game_datetime.isnot(None)
            ).limit(100)  # Start with first 100 to test
            
            for game in games_without_weather:
                # Get team names
                home_team = db.query(Team).filter(Team.team_uid == game.home_team_uid).first()
                away_team = db.query(Team).filter(Team.team_uid == game.away_team_uid).first()
                
                if not home_team or not away_team:
                    continue
                
                home_team_name = f"{home_team.city} {home_team.name}"
                away_team_name = f"{away_team.city} {away_team.name}"
                
                logger.info(f"Searching: {away_team_name} @ {home_team_name} on {game.game_datetime.date()}")
                
                # Try to get game data from ESPN
                competition_data = await self.get_game_data_by_date(
                    game.game_datetime, 
                    home_team_name, 
                    away_team_name
                )
                
                if competition_data:
                    self.stats["games_found"] += 1
                    updated_fields = 0
                    
                    # Extract weather data
                    weather_info = competition_data.get('weather')
                    if weather_info:
                        if game.weather_temp is None and weather_info.get('temperature'):
                            try:
                                temp = int(weather_info['temperature'])
                                game.weather_temp = temp
                                updated_fields += 1
                                logger.info(f"    Added temperature: {temp}°F")
                            except (ValueError, TypeError):
                                pass
                        
                        if game.weather_condition is None and weather_info.get('displayValue'):
                            condition = weather_info['displayValue'].lower()
                            # Normalize weather conditions
                            if 'clear' in condition or 'sunny' in condition:
                                game.weather_condition = 'clear'
                            elif 'rain' in condition or 'storm' in condition:
                                game.weather_condition = 'rain'
                            elif 'snow' in condition:
                                game.weather_condition = 'snow'
                            elif 'cloud' in condition or 'overcast' in condition:
                                game.weather_condition = 'cloudy'
                            elif 'wind' in condition:
                                game.weather_condition = 'windy'
                            else:
                                game.weather_condition = condition
                            
                            updated_fields += 1
                            logger.info(f"    Added weather condition: {game.weather_condition}")
                    
                    # Extract venue data
                    venue_info = competition_data.get('venue')
                    if venue_info and game.venue is None:
                        venue_name = venue_info.get('fullName')
                        if venue_name:
                            game.venue = venue_name
                            updated_fields += 1
                            logger.info(f"    Added venue: {venue_name}")
                    
                    # Verify attendance if available
                    attendance = competition_data.get('attendance')
                    if attendance and isinstance(attendance, int):
                        if game.attendance != attendance:
                            logger.info(f"    Attendance verification: DB={game.attendance}, ESPN={attendance}")
                            # Only update if ESPN attendance is significantly different and seems reasonable
                            if abs(game.attendance - attendance) > 5000 and attendance > 30000:
                                game.attendance = attendance
                                updated_fields += 1
                                self.stats["attendance_verified"] += 1
                    
                    if updated_fields > 0:
                        game.updated_at = datetime.utcnow()
                        fields_updated += updated_fields
                        
                        if weather_info:
                            self.stats["weather_data_added"] += 1
                        if venue_info:
                            self.stats["venue_data_added"] += 1
            
            if fields_updated > 0:
                db.commit()
                logger.info(f"  ✅ Updated {fields_updated} fields from ESPN API")
        
        return fields_updated
    
    async def collect_enhanced_data(self) -> Dict:
        """Run enhanced ESPN API data collection"""
        
        logger.info("Starting enhanced ESPN API data collection...")
        
        results = {
            "weather_fields_added": 0,
            "venue_fields_added": 0,
            "attendance_verified": 0,
            "total_api_calls": 0,
            "games_matched": 0
        }
        
        # Collect missing weather data
        weather_fields = await self.collect_missing_weather_data()
        
        results.update({
            "weather_fields_added": self.stats["weather_data_added"],
            "venue_fields_added": self.stats["venue_data_added"],
            "attendance_verified": self.stats["attendance_verified"],
            "total_api_calls": self.stats["api_calls_made"],
            "games_matched": self.stats["games_found"],
            "total_fields_updated": self.stats["total_fields_updated"]
        })
        
        return results

async def main():
    """Main execution"""
    logger.info("=" * 80)
    logger.info("ENHANCED ESPN API DATA COLLECTION")
    logger.info("=" * 80)
    logger.info("Based on Public-ESPN-API documentation")
    logger.info("Focus: Historical weather data and venue information")
    
    try:
        async with ESPNAPICollector() as collector:
            results = await collector.collect_enhanced_data()
            
            logger.info("\n" + "=" * 60)
            logger.info("ENHANCED ESPN COLLECTION COMPLETE")
            logger.info("=" * 60)
            
            logger.info(f"API calls made: {results['total_api_calls']}")
            logger.info(f"Games matched: {results['games_matched']}")
            logger.info(f"Weather fields added: {results['weather_fields_added']}")
            logger.info(f"Venue fields added: {results['venue_fields_added']}")
            logger.info(f"Attendance verified: {results['attendance_verified']}")
            
            # Check final coverage
            with SessionLocal() as db:
                total_games = db.query(Game).count()
                with_weather = db.query(Game).filter(Game.weather_condition.isnot(None)).count()
                with_venue = db.query(Game).filter(Game.venue.isnot(None)).count()
                
                weather_pct = (with_weather / total_games) * 100
                venue_pct = (with_venue / total_games) * 100
                
                logger.info(f"\n📊 Updated Coverage:")
                logger.info(f"   Weather: {with_weather}/{total_games} ({weather_pct:.1f}%)")
                logger.info(f"   Venue: {with_venue}/{total_games} ({venue_pct:.1f}%)")
            
            if results['games_matched'] > 0:
                logger.info("\n🎯 ESPN API ENHANCEMENT SUCCESSFUL!")
                logger.info("✅ Improved data coverage using historical ESPN endpoints")
            else:
                logger.info("\n⚠️  No additional data found")
                logger.info("ESPN API may not have historical data for these seasons")
            
            return 0
        
    except Exception as e:
        logger.error(f"❌ Collection failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)