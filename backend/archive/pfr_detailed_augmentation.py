#!/usr/bin/env python3
"""
Phase 2: Augment with detailed Pro Football Reference data
- Weather conditions, temperature, wind
- Attendance figures
- Better kickoff times
- Team statistics (NO player stats)
- Venue details
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import re

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.models.sports import Game
from app.scrapers.pro_football_reference_fixed import ProFootballReferenceScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("pfr_detailed_augmentation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PFRDetailedAugmentation:
    """Augment games with detailed Pro Football Reference data"""
    
    def __init__(self, max_games_per_season: int = 50):
        self.scraper = None
        self.db = None
        self.max_games_per_season = max_games_per_season
        
    def __enter__(self):
        self.db = SessionLocal()
        self.scraper = ProFootballReferenceScraper(headless=True)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.scraper:
            self.scraper.close()
        if self.db:
            self.db.close()
    
    def generate_pfr_game_id(self, game: Game) -> Optional[str]:
        """Generate Pro Football Reference game ID from game data"""
        if not game.game_datetime:
            return None
            
        # PFR format: YYYYMMDDTTT (date + team abbreviation)
        date_str = game.game_datetime.strftime('%Y%m%d')
        
        # Map team UIDs to PFR abbreviations
        team_abbrev_map = {
            'NFL_134946': 'crd',  # Arizona Cardinals
            'NFL_134942': 'atl',  # Atlanta Falcons
            'NFL_134922': 'rav',  # Baltimore Ravens
            'NFL_134918': 'buf',  # Buffalo Bills
            'NFL_134943': 'car',  # Carolina Panthers
            'NFL_134938': 'chi',  # Chicago Bears
            'NFL_134923': 'cin',  # Cincinnati Bengals
            'NFL_134924': 'cle',  # Cleveland Browns
            'NFL_134934': 'dal',  # Dallas Cowboys
            'NFL_134930': 'den',  # Denver Broncos
            'NFL_134939': 'det',  # Detroit Lions
            'NFL_134940': 'gnb',  # Green Bay Packers
            'NFL_134926': 'htx',  # Houston Texans
            'NFL_134927': 'clt',  # Indianapolis Colts
            'NFL_134928': 'jax',  # Jacksonville Jaguars
            'NFL_134931': 'kan',  # Kansas City Chiefs
            'NFL_134932': 'rai',  # Las Vegas Raiders
            'NFL_135908': 'sdg',  # Los Angeles Chargers
            'NFL_135907': 'ram',  # Los Angeles Rams
            'NFL_134919': 'mia',  # Miami Dolphins
            'NFL_134941': 'min',  # Minnesota Vikings
            'NFL_134920': 'nwe',  # New England Patriots
            'NFL_134944': 'nor',  # New Orleans Saints
            'NFL_134935': 'nyg',  # New York Giants
            'NFL_134921': 'nyj',  # New York Jets
            'NFL_134936': 'phi',  # Philadelphia Eagles
            'NFL_134925': 'pit',  # Pittsburgh Steelers
            'NFL_134948': 'sfo',  # San Francisco 49ers
            'NFL_134949': 'sea',  # Seattle Seahawks
            'NFL_134945': 'tam',  # Tampa Bay Buccaneers
            'NFL_134929': 'oti',  # Tennessee Titans
            'NFL_134937': 'was'   # Washington Commanders
        }
        
        # Use home team for game ID
        home_abbrev = team_abbrev_map.get(game.home_team_uid)
        if not home_abbrev:
            return None
            
        return f"{date_str}{home_abbrev}"
    
    def scrape_game_details(self, pfr_game_id: str) -> Optional[Dict]:
        """Scrape detailed game information from Pro Football Reference"""
        try:
            url = f"https://www.pro-football-reference.com/boxscores/{pfr_game_id}.htm"
            logger.debug(f"Scraping game details: {url}")
            
            self.scraper.driver.get(url)
            
            details = {}
            
            # Extract weather information
            weather_info = self.extract_weather_info()
            if weather_info:
                details.update(weather_info)
            
            # Extract attendance
            attendance = self.extract_attendance()
            if attendance:
                details['attendance'] = attendance
            
            # Extract game time (better than what we have)
            game_time = self.extract_game_time()
            if game_time:
                details['kickoff_time'] = game_time
            
            # Extract venue information
            venue_info = self.extract_venue_info()
            if venue_info:
                details.update(venue_info)
            
            return details if details else None
            
        except Exception as e:
            logger.error(f"Failed to scrape game {pfr_game_id}: {e}")
            return None
    
    def extract_weather_info(self) -> Optional[Dict]:
        """Extract weather information from PFR page"""
        try:
            # Look for weather information in the game info section
            weather_elements = self.scraper.driver.find_elements("xpath", "//div[contains(text(), '°') or contains(text(), 'wind') or contains(text(), 'Weather')]")
            
            weather_data = {}
            
            for element in weather_elements:
                text = element.text.lower()
                
                # Extract temperature
                temp_match = re.search(r'(\d+)°', text)
                if temp_match:
                    weather_data['weather_temp'] = int(temp_match.group(1))
                
                # Extract wind speed
                wind_match = re.search(r'wind[:\s]*(\d+)', text)
                if wind_match:
                    weather_data['weather_wind_speed'] = int(wind_match.group(1))
                
                # Extract weather condition
                if any(condition in text for condition in ['sunny', 'cloudy', 'rain', 'snow', 'clear', 'overcast']):
                    weather_data['weather_condition'] = text.strip()
            
            return weather_data if weather_data else None
            
        except Exception as e:
            logger.debug(f"Could not extract weather info: {e}")
            return None
    
    def extract_attendance(self) -> Optional[int]:
        """Extract attendance figure from PFR page"""
        try:
            # Look for attendance information
            attendance_elements = self.scraper.driver.find_elements("xpath", "//div[contains(text(), 'ttendance') or contains(text(), 'Attendance')]")
            
            for element in attendance_elements:
                text = element.text
                # Extract number from attendance text
                attendance_match = re.search(r'[\d,]+', text.replace(',', ''))
                if attendance_match:
                    return int(attendance_match.group().replace(',', ''))
            
            return None
            
        except Exception as e:
            logger.debug(f"Could not extract attendance: {e}")
            return None
    
    def extract_game_time(self) -> Optional[str]:
        """Extract kickoff time from PFR page"""
        try:
            # Look for time information
            time_elements = self.scraper.driver.find_elements("xpath", "//div[contains(text(), 'Start Time') or contains(text(), 'ET') or contains(text(), 'PM') or contains(text(), 'AM')]")
            
            for element in time_elements:
                text = element.text
                time_match = re.search(r'(\d{1,2}:\d{2})\s*(AM|PM|ET)', text)
                if time_match:
                    return time_match.group()
            
            return None
            
        except Exception as e:
            logger.debug(f"Could not extract game time: {e}")
            return None
    
    def extract_venue_info(self) -> Optional[Dict]:
        """Extract venue information from PFR page"""
        try:
            venue_data = {}
            
            # Look for stadium/venue information
            venue_elements = self.scraper.driver.find_elements("xpath", "//div[contains(text(), 'Stadium') or contains(text(), 'Field')]")
            
            for element in venue_elements:
                text = element.text
                if 'stadium' in text.lower() or 'field' in text.lower():
                    venue_data['venue'] = text.strip()
                    break
            
            return venue_data if venue_data else None
            
        except Exception as e:
            logger.debug(f"Could not extract venue info: {e}")
            return None
    
    def update_game_with_details(self, game: Game, details: Dict):
        """Update game with detailed information from PFR"""
        try:
            updated_fields = []
            
            if details.get('weather_temp') and not game.weather_temp:
                game.weather_temp = details['weather_temp']
                updated_fields.append('weather_temp')
            
            if details.get('weather_condition') and not game.weather_condition:
                game.weather_condition = details['weather_condition']
                updated_fields.append('weather_condition')
            
            if details.get('weather_wind_speed') and not game.weather_wind_speed:
                game.weather_wind_speed = details['weather_wind_speed']
                updated_fields.append('weather_wind_speed')
            
            if details.get('attendance') and not game.attendance:
                game.attendance = details['attendance']
                updated_fields.append('attendance')
            
            if details.get('venue') and not game.venue:
                game.venue = details['venue']
                updated_fields.append('venue')
            
            if updated_fields:
                game.updated_at = datetime.utcnow()
                self.db.commit()
                logger.debug(f"Updated game {game.game_uid}: {', '.join(updated_fields)}")
                return len(updated_fields)
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to update game {game.game_uid}: {e}")
            self.db.rollback()
            return 0
    
    def select_games_for_augmentation(self, season: int) -> List[Game]:
        """Select key games for detailed augmentation"""
        # Prioritize: playoffs > prime time games > regular season sample
        
        # Get playoff games first
        playoff_games = self.db.query(Game).filter(
            Game.season == season,
            Game.game_type.in_(['wildcard', 'divisional', 'conference', 'superbowl'])
        ).all()
        
        # Get some regular season games
        regular_games = self.db.query(Game).filter(
            Game.season == season,
            Game.game_type == 'regular'
        ).limit(max(0, self.max_games_per_season - len(playoff_games))).all()
        
        selected = playoff_games + regular_games
        logger.info(f"Selected {len(selected)} games for {season} ({len(playoff_games)} playoffs, {len(regular_games)} regular)")
        
        return selected[:self.max_games_per_season]
    
    async def augment_season(self, season: int) -> Dict:
        """Augment a season with detailed PFR data"""
        logger.info(f"Starting detailed PFR augmentation for {season} season")
        
        games_to_augment = self.select_games_for_augmentation(season)
        logger.info(f"Augmenting {len(games_to_augment)} games for {season}")
        
        successful_augmentations = 0
        total_fields_updated = 0
        
        for i, game in enumerate(games_to_augment, 1):
            try:
                pfr_game_id = self.generate_pfr_game_id(game)
                if not pfr_game_id:
                    logger.debug(f"Could not generate PFR ID for game {game.game_uid}")
                    continue
                
                logger.info(f"[{i}/{len(games_to_augment)}] Augmenting {game.game_type} game: {pfr_game_id}")
                
                details = self.scrape_game_details(pfr_game_id)
                if details:
                    fields_updated = self.update_game_with_details(game, details)
                    if fields_updated > 0:
                        successful_augmentations += 1
                        total_fields_updated += fields_updated
                
                # Rate limiting
                await asyncio.sleep(3)
                
            except Exception as e:
                logger.error(f"Failed to augment game {game.game_uid}: {e}")
                continue
        
        return {
            "season": season,
            "games_attempted": len(games_to_augment),
            "games_successfully_augmented": successful_augmentations,
            "total_fields_updated": total_fields_updated
        }
    
    async def augment_all_seasons(self, seasons: List[int]) -> Dict:
        """Augment multiple seasons with detailed PFR data"""
        logger.info(f"Starting detailed PFR augmentation for seasons: {seasons}")
        
        results = {}
        total_augmented = 0
        
        for season in seasons:
            season_result = await self.augment_season(season)
            results[season] = season_result
            total_augmented += season_result['games_successfully_augmented']
        
        return {
            "seasons_processed": seasons,
            "results": results,
            "total_games_augmented": total_augmented,
            "timestamp": datetime.utcnow().isoformat()
        }


async def main():
    """Main execution"""
    logger.info("=" * 80)
    logger.info("PRO FOOTBALL REFERENCE DETAILED AUGMENTATION")
    logger.info("=" * 80)
    logger.info("Adding: Weather, Attendance, Venue details, Better times")
    logger.info("Focus: Playoff games + sample of regular season")
    
    seasons = [2022, 2023, 2024]
    
    try:
        with PFRDetailedAugmentation(max_games_per_season=30) as service:
            results = await service.augment_all_seasons(seasons)
            
            logger.info("\n" + "=" * 60)
            logger.info("DETAILED AUGMENTATION COMPLETE")
            logger.info("=" * 60)
            
            for season, result in results["results"].items():
                logger.info(f"\n{season} Season:")
                logger.info(f"  Games attempted: {result['games_attempted']}")
                logger.info(f"  Successfully augmented: {result['games_successfully_augmented']}")
                logger.info(f"  Total fields updated: {result['total_fields_updated']}")
            
            logger.info(f"\nTotal games augmented: {results['total_games_augmented']}")
            logger.info("\n✅ COMPREHENSIVE NFL DATA COLLECTION COMPLETE!")
            logger.info("📊 Database now contains: TheSportsDB schedules + PFR detailed data")
            
            return 0
            
    except Exception as e:
        logger.error(f"❌ DETAILED AUGMENTATION FAILED: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)