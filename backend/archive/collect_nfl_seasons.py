#!/usr/bin/env python3
"""
Collect multiple NFL seasons using TheSportsDB as primary source
Handles any season from 1960 to present
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import List

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.services.thesportsdb_data_collector import TheSportsDBDataCollector, TheSportsDBDataCollectionManager
from app.core.database import engine
from app.models.sports import Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("nfl_seasons_collection.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize database tables"""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully!")


async def collect_nfl_seasons(seasons: List[int]):
    """
    Collect NFL seasons using TheSportsDB V2 API
    
    Args:
        seasons: List of season years to collect (e.g., [2022, 2023, 2024])
    """
    logger.info("=" * 80)
    logger.info(f"NFL SEASONS COLLECTION - {len(seasons)} SEASONS")
    logger.info("=" * 80)
    logger.info(f"Seasons to collect: {seasons}")
    logger.info("Data sources:")
    logger.info("- TheSportsDB V2 API: Complete schedules and results")
    logger.info("- Pro Football Reference: Team statistics (separate process)")
    
    try:
        # Initialize database
        init_database()
        
        # Collect each season
        total_games_collected = 0
        
        for season in seasons:
            logger.info(f"\n{'='*60}")
            logger.info(f"COLLECTING {season} NFL SEASON")
            logger.info(f"{'='*60}")
            
            with TheSportsDBDataCollector() as collector:
                season_result = await collector.collect_complete_season_data(season, force_refresh=True)
                
                if season_result.get("status") == "completed":
                    thesportsdb_data = season_result.get("thesportsdb_schedule", {})
                    verification = season_result.get("verification", {})
                    
                    games_collected = thesportsdb_data.get('games_collected', 0)
                    total_games = verification.get('total_games', 0)
                    
                    logger.info(f"\n{season} Season Results:")
                    logger.info(f"  ✅ Games collected from TheSportsDB: {games_collected}")
                    logger.info(f"  ✅ Total games in database: {total_games}")
                    logger.info(f"  ✅ Regular season: {verification.get('regular_season', {}).get('count', 0)}")
                    logger.info(f"  ✅ Playoffs: {verification.get('playoffs', {}).get('count', 0)}")
                    
                    total_games_collected += total_games
                    
                else:
                    logger.error(f"  ❌ Failed to collect {season}: {season_result.get('error', 'Unknown error')}")
        
        # Final summary
        logger.info(f"\n{'='*80}")
        logger.info("NFL SEASONS COLLECTION COMPLETE - SUMMARY")
        logger.info(f"{'='*80}")
        logger.info(f"Seasons processed: {len(seasons)}")
        logger.info(f"Total games collected: {total_games_collected}")
        logger.info(f"Data source: TheSportsDB V2 API ✅")
        logger.info("\nNext steps:")
        logger.info("1. Run Pro Football Reference augmentation for detailed team stats")
        logger.info("2. Verify data quality and completeness")
        logger.info("3. Export for frontend consumption")
        
        return {
            "status": "success",
            "seasons_collected": seasons,
            "total_games": total_games_collected
        }
        
    except Exception as e:
        logger.error(f"❌ NFL SEASONS COLLECTION FAILED: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


async def main():
    """Main execution"""
    # Default to last 3 complete seasons
    # 2024 season is ongoing, so collect 2021, 2022, 2023
    default_seasons = [2021, 2022, 2023]
    
    # Allow command line override
    if len(sys.argv) > 1:
        try:
            seasons = [int(year) for year in sys.argv[1:]]
            # Validate years are reasonable (1960-2024)
            for year in seasons:
                if year < 1960 or year > 2024:
                    raise ValueError(f"Season {year} out of valid range (1960-2024)")
        except ValueError as e:
            logger.error(f"Invalid season years provided: {e}")
            logger.info(f"Usage: python {sys.argv[0]} [year1] [year2] ...")
            logger.info(f"Example: python {sys.argv[0]} 2021 2022 2023")
            return 1
    else:
        seasons = default_seasons
    
    try:
        results = await collect_nfl_seasons(seasons)
        
        if results["status"] == "success":
            logger.info("\n🚀 NFL SEASONS COLLECTION SUCCESSFUL!")
            return 0
        else:
            logger.error(f"\n💥 NFL SEASONS COLLECTION FAILED: {results['error']}")
            return 1
            
    except Exception as e:
        logger.error(f"💥 CRITICAL ERROR: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)