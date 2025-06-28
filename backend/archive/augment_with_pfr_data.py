#!/usr/bin/env python3
"""
Augment TheSportsDB data with Pro Football Reference granular data
- Fix game_type categorization (preseason, regular, playoffs)
- Populate game_datetime with actual dates/times
- Add team statistics, weather, attendance (NO player stats)
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.models.sports import Game
from app.scrapers.pro_football_reference_fixed import ProFootballReferenceScraper
from sqlalchemy import and_

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("pfr_augmentation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PFRAugmentationService:
    """Service to augment TheSportsDB data with Pro Football Reference details"""
    
    def __init__(self):
        self.scraper = None
        self.db = None
        
    def __enter__(self):
        self.db = SessionLocal()
        self.scraper = ProFootballReferenceScraper(headless=True)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.scraper:
            self.scraper.close()
        if self.db:
            self.db.close()
    
    def determine_game_type_from_date(self, game_date: datetime, season: int) -> str:
        """Determine game type based on date patterns"""
        if not game_date:
            return 'regular'
            
        month = game_date.month
        day = game_date.day
        
        # Preseason: August and early September
        if month == 8 or (month == 9 and day <= 10):
            return 'preseason'
        
        # Regular season: September through December
        elif month in [9, 10, 11, 12]:
            return 'regular'
        
        # Playoffs: January and February
        elif month in [1, 2]:
            # Determine specific playoff round based on date ranges
            if month == 1:
                if day <= 16:
                    return 'wildcard'
                elif day <= 23:
                    return 'divisional'
                elif day <= 31:
                    return 'conference'
            elif month == 2:
                if day <= 15:
                    return 'superbowl'
        
        return 'regular'  # Default fallback
    
    def get_pfr_season_data(self, season: int) -> List[Dict]:
        """Get complete season data from Pro Football Reference"""
        logger.info(f"Scraping {season} season data from Pro Football Reference")
        
        try:
            # Use the existing scraper to get season data
            url = f"https://www.pro-football-reference.com/years/{season}/games.htm"
            self.scraper.driver.get(url)
            
            # Extract game data - this will need to be implemented in the scraper
            # For now, return empty list and we'll implement step by step
            return []
            
        except Exception as e:
            logger.error(f"Failed to scrape PFR season data for {season}: {e}")
            return []
    
    def match_games_by_teams_and_date(self, thesportsdb_game: Game, pfr_games: List[Dict]) -> Optional[Dict]:
        """Match TheSportsDB game with PFR game based on teams and date"""
        # This is a placeholder - we'll implement the matching logic
        return None
    
    def update_game_with_pfr_data(self, game: Game, pfr_data: Dict):
        """Update game with Pro Football Reference data"""
        try:
            # Update game_datetime if we have better date/time info
            if pfr_data.get('game_datetime'):
                game.game_datetime = pfr_data['game_datetime']
            
            # Fix game_type categorization
            if pfr_data.get('game_type'):
                game.game_type = pfr_data['game_type']
            elif game.game_datetime:
                game.game_type = self.determine_game_type_from_date(game.game_datetime, game.season)
            
            # Add other PFR data (weather, attendance, etc.)
            if pfr_data.get('attendance'):
                game.attendance = pfr_data['attendance']
                
            if pfr_data.get('weather_condition'):
                game.weather_condition = pfr_data['weather_condition']
                
            if pfr_data.get('weather_temp'):
                game.weather_temp = pfr_data['weather_temp']
            
            # Update metadata
            game.updated_at = datetime.utcnow()
            
            self.db.commit()
            logger.debug(f"Updated game {game.game_uid} with PFR data")
            
        except Exception as e:
            logger.error(f"Failed to update game {game.game_uid}: {e}")
            self.db.rollback()
    
    async def augment_season(self, season: int) -> Dict:
        """Augment a specific season with PFR data"""
        logger.info(f"Starting PFR augmentation for {season} season")
        
        # Get all games for this season from database
        games = self.db.query(Game).filter(Game.season == season).all()
        logger.info(f"Found {len(games)} games in database for {season}")
        
        # First pass: Fix game_type based on existing game_datetime if available
        games_updated = 0
        games_needing_pfr = []
        
        for game in games:
            if game.game_datetime:
                # We have a date, determine correct game_type
                correct_type = self.determine_game_type_from_date(game.game_datetime, season)
                if game.game_type != correct_type:
                    logger.info(f"Fixing game_type for {game.game_uid}: {game.game_type} -> {correct_type}")
                    game.game_type = correct_type
                    games_updated += 1
            else:
                # No date available, need to get from PFR
                games_needing_pfr.append(game)
        
        if games_updated > 0:
            self.db.commit()
            logger.info(f"Fixed game_type for {games_updated} games based on existing dates")
        
        logger.info(f"{len(games_needing_pfr)} games need PFR augmentation for missing data")
        
        # For now, let's just return the summary
        # In the next phase, we'll implement full PFR matching
        return {
            "season": season,
            "total_games": len(games),
            "games_type_fixed": games_updated,
            "games_needing_pfr": len(games_needing_pfr),
            "status": "game_type_categorization_fixed"
        }
    
    async def augment_all_seasons(self, seasons: List[int]) -> Dict:
        """Augment multiple seasons with PFR data"""
        logger.info(f"Starting PFR augmentation for seasons: {seasons}")
        
        results = {}
        total_updated = 0
        
        for season in seasons:
            season_result = await self.augment_season(season)
            results[season] = season_result
            total_updated += season_result.get('games_type_fixed', 0)
            
            # Rate limiting between seasons
            await asyncio.sleep(1)
        
        return {
            "seasons_processed": seasons,
            "results": results,
            "total_games_updated": total_updated,
            "timestamp": datetime.utcnow().isoformat()
        }


async def main():
    """Main execution"""
    logger.info("=" * 80)
    logger.info("PRO FOOTBALL REFERENCE AUGMENTATION")
    logger.info("=" * 80)
    logger.info("Phase 1: Fix game_type categorization")
    logger.info("Phase 2: Add missing dates and granular data (next step)")
    
    # Process the three seasons we have
    seasons = [2022, 2023, 2024]
    
    try:
        with PFRAugmentationService() as service:
            results = await service.augment_all_seasons(seasons)
            
            logger.info("\n" + "=" * 60)
            logger.info("AUGMENTATION COMPLETE - SUMMARY")
            logger.info("=" * 60)
            
            for season, result in results["results"].items():
                logger.info(f"\n{season} Season:")
                logger.info(f"  Total games: {result['total_games']}")
                logger.info(f"  Game types fixed: {result['games_type_fixed']}")
                logger.info(f"  Need PFR data: {result['games_needing_pfr']}")
            
            logger.info(f"\nTotal games updated: {results['total_games_updated']}")
            logger.info("\n✅ Phase 1 Complete: Game type categorization fixed")
            logger.info("🔄 Next: Implement full PFR matching for dates and granular data")
            
            return 0
            
    except Exception as e:
        logger.error(f"❌ AUGMENTATION FAILED: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)