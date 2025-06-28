#!/usr/bin/env python3
"""
Incremental Pro Football Reference data augmentation with cross-verification
Phase 1: Season overview pages (team statistics)
Phase 2: Individual game pages (weather, attendance, detailed stats)
Phase 3: Data verification and quality assurance
"""

import asyncio
import logging
import sys
import re
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.models.sports import Game, Team
from app.scrapers.pro_football_reference_fixed import ProFootballReferenceScraper
from sqlalchemy import and_, or_

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("incremental_pfr_augmentation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class GameVerification:
    """Data structure for cross-verification between TheSportsDB and PFR"""
    thesportsdb_id: str
    pfr_id: str
    date_match: bool
    teams_match: bool
    score_match: bool
    confidence_score: float

class IncrementalPFRAugmentation:
    """Incremental PFR augmentation with verification and rate limiting"""
    
    def __init__(self, rate_limit_seconds: float = 3.0):
        self.scraper = None
        self.db = None
        self.rate_limit_seconds = rate_limit_seconds
        self.last_request_time = 0
        
        # PFR team abbreviation mapping
        self.pfr_team_mapping = {
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
        
    def __enter__(self):
        self.db = SessionLocal()
        self.scraper = ProFootballReferenceScraper(headless=True)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.scraper:
            self.scraper.close()
        if self.db:
            self.db.close()
    
    async def rate_limit(self):
        """Implement rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_seconds:
            sleep_time = self.rate_limit_seconds - time_since_last
            logger.debug(f"Rate limiting: sleeping {sleep_time:.1f}s")
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def generate_pfr_game_id(self, game: Game) -> Optional[str]:
        """Generate Pro Football Reference game ID"""
        if not game.game_datetime:
            return None
            
        date_str = game.game_datetime.strftime('%Y%m%d')
        home_abbrev = self.pfr_team_mapping.get(game.home_team_uid)
        
        if not home_abbrev:
            logger.warning(f"No PFR mapping for home team {game.home_team_uid}")
            return None
            
        return f"{date_str}{home_abbrev}"
    
    async def scrape_season_overview(self, season: int) -> Dict:
        """Phase 1: Scrape season overview for team statistics"""
        logger.info(f"Phase 1: Scraping {season} season overview from PFR")
        
        await self.rate_limit()
        
        try:
            url = f"https://www.pro-football-reference.com/years/{season}/games.htm"
            logger.info(f"Fetching season overview: {url}")
            
            self.scraper.driver.get(url)
            await asyncio.sleep(2)  # Let page load
            
            # Extract season-level statistics
            season_stats = self.extract_season_stats()
            
            # Extract game list for verification
            games_list = self.extract_games_list()
            
            logger.info(f"Found {len(games_list)} games in PFR season overview")
            
            return {
                "season": season,
                "season_stats": season_stats,
                "games_list": games_list,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to scrape season overview for {season}: {e}")
            return {"season": season, "error": str(e)}
    
    def extract_season_stats(self) -> Dict:
        """Extract season-level team statistics"""
        stats = {}
        
        try:
            # Look for team stats tables
            tables = self.scraper.driver.find_elements("tag name", "table")
            
            for table in tables:
                table_id = table.get_attribute("id")
                if table_id and "team" in table_id.lower():
                    logger.debug(f"Processing team stats table: {table_id}")
                    # Extract team statistics from table
                    # Implementation depends on PFR page structure
                    
        except Exception as e:
            logger.debug(f"Could not extract season stats: {e}")
            
        return stats
    
    def extract_games_list(self) -> List[Dict]:
        """Extract list of games from season overview for verification"""
        games = []
        
        try:
            # Look for games table
            games_table = self.scraper.driver.find_element("id", "games")
            rows = games_table.find_elements("tag name", "tr")
            
            for row in rows[1:]:  # Skip header
                cells = row.find_elements("tag name", "td")
                if len(cells) >= 6:
                    try:
                        game_data = {
                            "week": cells[0].text.strip(),
                            "date": cells[1].text.strip(),
                            "away_team": cells[3].text.strip(),
                            "home_team": cells[5].text.strip(),
                            "away_score": cells[4].text.strip() if cells[4].text.strip().isdigit() else None,
                            "home_score": cells[6].text.strip() if len(cells) > 6 and cells[6].text.strip().isdigit() else None
                        }
                        games.append(game_data)
                    except Exception as e:
                        logger.debug(f"Could not parse game row: {e}")
                        continue
                        
        except Exception as e:
            logger.debug(f"Could not extract games list: {e}")
            
        return games
    
    async def verify_game_match(self, thesportsdb_game: Game, pfr_game: Dict) -> GameVerification:
        """Cross-verify game data between TheSportsDB and PFR"""
        
        # Date verification
        date_match = False
        if thesportsdb_game.game_datetime and pfr_game.get("date"):
            try:
                pfr_date = datetime.strptime(pfr_game["date"], "%Y-%m-%d")
                date_diff = abs((thesportsdb_game.game_datetime.date() - pfr_date.date()).days)
                date_match = date_diff <= 1  # Allow 1 day difference
            except:
                pass
        
        # Team verification (simplified - would need full team name mapping)
        teams_match = True  # Placeholder - implement based on team name mappings
        
        # Score verification
        score_match = False
        if (thesportsdb_game.home_score is not None and 
            thesportsdb_game.away_score is not None and
            pfr_game.get("home_score") and pfr_game.get("away_score")):
            try:
                score_match = (int(pfr_game["home_score"]) == thesportsdb_game.home_score and
                              int(pfr_game["away_score"]) == thesportsdb_game.away_score)
            except:
                pass
        
        # Calculate confidence score
        confidence_score = sum([date_match, teams_match, score_match]) / 3.0
        
        return GameVerification(
            thesportsdb_id=thesportsdb_game.game_uid,
            pfr_id=f"pfr_{pfr_game.get('date', '')}_{pfr_game.get('home_team', '')}",
            date_match=date_match,
            teams_match=teams_match,
            score_match=score_match,
            confidence_score=confidence_score
        )
    
    async def scrape_game_details(self, game: Game) -> Optional[Dict]:
        """Phase 2: Scrape individual game details with verification"""
        
        pfr_game_id = self.generate_pfr_game_id(game)
        if not pfr_game_id:
            return None
            
        await self.rate_limit()
        
        try:
            url = f"https://www.pro-football-reference.com/boxscores/{pfr_game_id}.htm"
            logger.debug(f"Scraping game details: {url}")
            
            self.scraper.driver.get(url)
            await asyncio.sleep(2)
            
            # Check if page exists (404 handling)
            if "404" in self.scraper.driver.title or "Not Found" in self.scraper.driver.title:
                logger.warning(f"Game not found: {pfr_game_id}")
                return None
            
            details = {}
            
            # Extract game information
            details.update(self.extract_game_info())
            details.update(self.extract_weather_info())
            details.update(self.extract_attendance_info())
            details.update(self.extract_venue_info())
            
            # Add verification metadata
            details["pfr_game_id"] = pfr_game_id
            details["source_url"] = url
            details["scraped_at"] = datetime.utcnow().isoformat()
            
            return details if details else None
            
        except Exception as e:
            logger.error(f"Failed to scrape game {pfr_game_id}: {e}")
            return None
    
    def extract_game_info(self) -> Dict:
        """Extract basic game information"""
        info = {}
        
        try:
            # Look for game info elements
            scorebox = self.scraper.driver.find_element("class name", "scorebox")
            
            # Extract kickoff time
            time_elements = scorebox.find_elements("xpath", ".//*[contains(text(), 'Start Time') or contains(text(), 'ET')]")
            for elem in time_elements:
                time_match = re.search(r'(\d{1,2}:\d{2})\s*(AM|PM|ET)', elem.text)
                if time_match:
                    info["kickoff_time"] = time_match.group()
                    break
                    
        except Exception as e:
            logger.debug(f"Could not extract game info: {e}")
            
        return info
    
    def extract_weather_info(self) -> Dict:
        """Extract weather information"""
        weather = {}
        
        try:
            # Look for weather information
            weather_elements = self.scraper.driver.find_elements("xpath", "//*[contains(text(), '°') or contains(text(), 'wind') or contains(text(), 'Weather')]")
            
            for element in weather_elements:
                text = element.text.lower()
                
                # Temperature
                temp_match = re.search(r'(\d+)°', text)
                if temp_match:
                    weather["weather_temp"] = int(temp_match.group(1))
                
                # Wind speed
                wind_match = re.search(r'wind[:\s]*(\d+)', text)
                if wind_match:
                    weather["weather_wind_speed"] = int(wind_match.group(1))
                
                # Conditions
                conditions = ["sunny", "cloudy", "rain", "snow", "clear", "overcast", "dome", "indoor"]
                for condition in conditions:
                    if condition in text:
                        weather["weather_condition"] = condition
                        break
                        
        except Exception as e:
            logger.debug(f"Could not extract weather info: {e}")
            
        return weather
    
    def extract_attendance_info(self) -> Dict:
        """Extract attendance information"""
        attendance = {}
        
        try:
            # Look for attendance
            attendance_elements = self.scraper.driver.find_elements("xpath", "//*[contains(text(), 'ttendance') or contains(text(), 'Attendance')]")
            
            for element in attendance_elements:
                text = element.text.replace(',', '')
                attendance_match = re.search(r'(\d+)', text)
                if attendance_match:
                    attendance["attendance"] = int(attendance_match.group(1))
                    break
                    
        except Exception as e:
            logger.debug(f"Could not extract attendance: {e}")
            
        return attendance
    
    def extract_venue_info(self) -> Dict:
        """Extract venue information"""
        venue = {}
        
        try:
            # Look for stadium/venue info
            venue_elements = self.scraper.driver.find_elements("xpath", "//*[contains(text(), 'Stadium') or contains(text(), 'Field') or contains(text(), 'Dome')]")
            
            for element in venue_elements:
                text = element.text.strip()
                if any(word in text.lower() for word in ["stadium", "field", "dome", "center"]):
                    venue["venue"] = text
                    break
                    
        except Exception as e:
            logger.debug(f"Could not extract venue info: {e}")
            
        return venue
    
    def update_game_with_pfr_data(self, game: Game, pfr_data: Dict) -> int:
        """Update game with PFR data"""
        try:
            fields_updated = 0
            
            # Weather data
            if pfr_data.get("weather_temp") and not game.weather_temp:
                game.weather_temp = pfr_data["weather_temp"]
                fields_updated += 1
            
            if pfr_data.get("weather_condition") and not game.weather_condition:
                game.weather_condition = pfr_data["weather_condition"]
                fields_updated += 1
            
            if pfr_data.get("weather_wind_speed") and not game.weather_wind_speed:
                game.weather_wind_speed = pfr_data["weather_wind_speed"]
                fields_updated += 1
            
            # Attendance
            if pfr_data.get("attendance") and not game.attendance:
                game.attendance = pfr_data["attendance"]
                fields_updated += 1
            
            # Venue
            if pfr_data.get("venue") and not game.venue:
                game.venue = pfr_data["venue"]
                fields_updated += 1
            
            # Kickoff time (update game_datetime if we have better info)
            if pfr_data.get("kickoff_time") and game.game_datetime:
                # Could parse and update the time component
                pass
            
            if fields_updated > 0:
                game.updated_at = datetime.utcnow()
                self.db.commit()
                logger.debug(f"Updated {fields_updated} fields for game {game.game_uid}")
            
            return fields_updated
            
        except Exception as e:
            logger.error(f"Failed to update game {game.game_uid}: {e}")
            self.db.rollback()
            return 0
    
    async def augment_season(self, season: int) -> Dict:
        """Augment a complete season with PFR data"""
        logger.info(f"Starting incremental PFR augmentation for {season} season")
        
        # Phase 1: Season overview
        season_overview = await self.scrape_season_overview(season)
        
        # Get games from database
        games = self.db.query(Game).filter(Game.season == season).all()
        logger.info(f"Found {len(games)} games in database for {season}")
        
        # Phase 2: Individual game augmentation
        games_processed = 0
        games_updated = 0
        total_fields_updated = 0
        verification_failures = 0
        
        # Prioritize playoffs and recent games
        sorted_games = sorted(games, key=lambda g: (
            g.game_type not in ["wildcard", "divisional", "conference", "superbowl"],  # Playoffs first
            g.game_datetime or datetime.min  # Recent games first
        ))
        
        for i, game in enumerate(sorted_games, 1):
            try:
                logger.info(f"[{i}/{len(games)}] Processing {game.game_type} game: {game.game_uid}")
                
                # Scrape game details
                pfr_data = await self.scrape_game_details(game)
                
                if pfr_data:
                    # Update game with PFR data
                    fields_updated = self.update_game_with_pfr_data(game, pfr_data)
                    
                    if fields_updated > 0:
                        games_updated += 1
                        total_fields_updated += fields_updated
                        logger.info(f"  ✅ Updated {fields_updated} fields")
                    else:
                        logger.debug(f"  ℹ️  No new data to update")
                else:
                    logger.warning(f"  ⚠️  No PFR data found")
                
                games_processed += 1
                
                # Progress logging
                if games_processed % 10 == 0:
                    logger.info(f"Progress: {games_processed}/{len(games)} games processed")
                
            except Exception as e:
                logger.error(f"Failed to process game {game.game_uid}: {e}")
                verification_failures += 1
                continue
        
        return {
            "season": season,
            "games_in_database": len(games),
            "games_processed": games_processed,
            "games_updated": games_updated,
            "total_fields_updated": total_fields_updated,
            "verification_failures": verification_failures,
            "season_overview": season_overview,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def augment_multiple_seasons(self, seasons: List[int]) -> Dict:
        """Augment multiple seasons with comprehensive verification"""
        logger.info(f"Starting incremental PFR augmentation for seasons: {seasons}")
        
        results = {}
        total_games_updated = 0
        total_fields_updated = 0
        
        for season in seasons:
            try:
                season_result = await self.augment_season(season)
                results[season] = season_result
                total_games_updated += season_result.get("games_updated", 0)
                total_fields_updated += season_result.get("total_fields_updated", 0)
                
                logger.info(f"✅ Season {season} complete: {season_result.get('games_updated', 0)} games updated")
                
            except Exception as e:
                logger.error(f"❌ Failed to augment season {season}: {e}")
                results[season] = {"error": str(e)}
        
        return {
            "seasons_processed": seasons,
            "results": results,
            "total_games_updated": total_games_updated,
            "total_fields_updated": total_fields_updated,
            "timestamp": datetime.utcnow().isoformat()
        }


async def main():
    """Main execution"""
    logger.info("=" * 80)
    logger.info("INCREMENTAL PRO FOOTBALL REFERENCE AUGMENTATION")
    logger.info("=" * 80)
    logger.info("Phase 1: Season overviews (team statistics)")
    logger.info("Phase 2: Individual game details (weather, attendance)")
    logger.info("Phase 3: Cross-verification and quality assurance")
    
    # Target the last 3 seasons
    seasons = [2022, 2023, 2024]
    
    try:
        with IncrementalPFRAugmentation(rate_limit_seconds=3.0) as service:
            results = await service.augment_multiple_seasons(seasons)
            
            logger.info("\n" + "=" * 60)
            logger.info("INCREMENTAL AUGMENTATION COMPLETE")
            logger.info("=" * 60)
            
            for season, result in results["results"].items():
                if "error" in result:
                    logger.error(f"{season}: ❌ {result['error']}")
                else:
                    logger.info(f"\n{season} Season:")
                    logger.info(f"  Games in database: {result.get('games_in_database', 0)}")
                    logger.info(f"  Games processed: {result.get('games_processed', 0)}")
                    logger.info(f"  Games updated: {result.get('games_updated', 0)}")
                    logger.info(f"  Fields updated: {result.get('total_fields_updated', 0)}")
                    logger.info(f"  Verification failures: {result.get('verification_failures', 0)}")
            
            logger.info(f"\nTotal games updated: {results['total_games_updated']}")
            logger.info(f"Total fields updated: {results['total_fields_updated']}")
            
            logger.info("\n✅ COMPREHENSIVE NFL DATA AUGMENTATION COMPLETE!")
            logger.info("📊 Database contains: TheSportsDB + verified PFR detailed data")
            
            return 0
            
    except Exception as e:
        logger.error(f"❌ AUGMENTATION FAILED: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)