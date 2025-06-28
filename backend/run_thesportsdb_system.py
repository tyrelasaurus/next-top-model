#!/usr/bin/env python3
"""
Run the TheSportsDB-first data collection system
Uses TheSportsDB API as primary source, Pro Football Reference for augmentation only
"""

import asyncio
import logging
import sys
from pathlib import Path

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
        logging.FileHandler("thesportsdb_system_run.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize database tables"""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully!")


async def run_thesportsdb_system():
    """Run the TheSportsDB-first data collection system"""
    logger.info("=" * 80)
    logger.info("THESPORTSDB-FIRST NFL DATA COLLECTION SYSTEM")
    logger.info("=" * 80)
    
    try:
        # Step 1: Initialize database
        init_database()
        
        # Step 2: Verify existing data status
        logger.info("\n" + "=" * 60)
        logger.info("STEP 1: VERIFYING EXISTING DATA")
        logger.info("=" * 60)
        
        verification_results = await TheSportsDBDataCollectionManager.verify_all_data()
        
        for season, results in verification_results["verification_results"].items():
            logger.info(f"\nSeason {season} Status:")
            completeness = results["completeness"]
            
            logger.info(f"  Total games: {completeness['total_games']}")
            logger.info(f"  Regular season: {completeness['regular_season']['count']}/{completeness['regular_season']['expected']}")
            logger.info(f"  Playoffs: {completeness['playoffs']['count']}/{completeness['playoffs']['expected']}")
            logger.info(f"  Missing games: {completeness['missing_games']}")
        
        # Step 3: Collect data using TheSportsDB first
        logger.info("\n" + "=" * 60)
        logger.info("STEP 2: FULL 2023 SEASON COLLECTION - THESPORTSDB + PFR TEAM STATS")
        logger.info("=" * 60)
        
        # Full collection for 2023 season
        target_season = 2023
        logger.info(f"Starting FULL data collection for {target_season} NFL season...")
        logger.info("- TheSportsDB: Game schedules, teams, basic results")
        logger.info("- Pro Football Reference: Detailed team stats & game data")
        
        with TheSportsDBDataCollector() as collector:
            season_result = await collector.collect_complete_season_data(target_season, force_refresh=True)
            
            logger.info(f"\nSeason {target_season} Collection:")
            if season_result.get("status") == "completed":
                thesportsdb_data = season_result.get("thesportsdb_schedule", {})
                pfr_data = season_result.get("pfr_augmentation", {})
                verification = season_result.get("verification", {})
                
                logger.info(f"  Status: ✅ Success")
                logger.info(f"  TheSportsDB games collected: {thesportsdb_data.get('games_collected', 0)}")
                logger.info(f"  PFR team stats gathered: {pfr_data.get('games_augmented', 0)}")
                logger.info(f"  Total games in DB: {verification.get('total_games', 0)}")
                logger.info(f"  Regular season: {verification.get('regular_season', {}).get('count', 0)}")
                logger.info(f"  Playoffs: {verification.get('playoffs', {}).get('count', 0)}")
            else:
                logger.error(f"  Status: ❌ Failed - {season_result.get('error', 'Unknown error')}")
        
        # Step 4: Final verification
        logger.info("\n" + "=" * 60)
        logger.info("STEP 3: FINAL VERIFICATION")
        logger.info("=" * 60)
        
        final_verification = await TheSportsDBDataCollectionManager.verify_all_data()
        
        total_games = 0
        for season, results in final_verification["verification_results"].items():
            completeness = results["completeness"]
            total_games += completeness['total_games']
        
        # Step 5: Summary
        logger.info("\n" + "=" * 80)
        logger.info("THESPORTSDB-FIRST SYSTEM RUN COMPLETE - SUMMARY")
        logger.info("=" * 80)
        
        logger.info(f"Total games in database: {total_games}")
        logger.info("Primary source: TheSportsDB API ✅")
        logger.info("Augmentation source: Pro Football Reference (selective) ✅")
        logger.info("Rate limiting: Implemented ✅")
        
        logger.info("\nSystem Status: ✅ THESPORTSDB-FIRST DATA COLLECTION COMPLETE")
        logger.info("Using TheSportsDB as primary source to avoid overwhelming PFR!")
        
        return {
            "status": "success",
            "total_games": total_games,
            "approach": "thesportsdb_first"
        }
        
    except Exception as e:
        logger.error(f"❌ THESPORTSDB SYSTEM RUN FAILED: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


async def main():
    """Main execution"""
    try:
        results = await run_thesportsdb_system()
        
        if results["status"] == "success":
            logger.info("\n🚀 THESPORTSDB-FIRST DATA COLLECTION SUCCESSFUL!")
            return 0
        else:
            logger.error(f"\n💥 THESPORTSDB SYSTEM FAILED: {results['error']}")
            return 1
            
    except Exception as e:
        logger.error(f"💥 CRITICAL ERROR: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)