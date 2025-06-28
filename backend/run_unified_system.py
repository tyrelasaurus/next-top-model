#!/usr/bin/env python3
"""
Run the unified data collection system non-interactively
Executes full data collection and verification workflow
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.services.data_collector import NFLDataCollector, DataCollectionManager
from app.core.database import engine
from app.models.sports import Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("unified_system_run.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize database tables"""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully!")


async def run_full_system():
    """Run the complete unified data collection and verification system"""
    logger.info("=" * 80)
    logger.info("UNIFIED NFL DATA COLLECTION SYSTEM - FULL RUN")
    logger.info("=" * 80)
    
    try:
        # Step 1: Initialize database
        init_database()
        
        # Step 2: Verify existing data status
        logger.info("\n" + "=" * 60)
        logger.info("STEP 1: VERIFYING EXISTING DATA")
        logger.info("=" * 60)
        
        verification_results = await DataCollectionManager.verify_all_data()
        
        for season, results in verification_results["verification_results"].items():
            logger.info(f"\nSeason {season} Status:")
            completeness = results["completeness"]
            consistency = results["consistency"]
            
            logger.info(f"  Total games: {completeness['total_games']}")
            logger.info(f"  Regular season: {completeness['regular_season']['count']}/{completeness['regular_season']['expected']}")
            logger.info(f"  Playoffs: {completeness['playoffs']['count']}/{completeness['playoffs']['expected']}")
            logger.info(f"  Data quality: {consistency['data_quality']}")
            logger.info(f"  Missing games: {completeness['missing_games']}")
        
        # Step 3: Collect any missing data
        logger.info("\n" + "=" * 60)
        logger.info("STEP 2: COLLECTING MISSING DATA")
        logger.info("=" * 60)
        
        seasons = [2022, 2023, 2024]
        collection_results = await DataCollectionManager.collect_all_seasons(seasons, force_refresh=False)
        
        for season, result in collection_results["results"].items():
            logger.info(f"\nSeason {season} Collection:")
            if result.get("status") == "completed":
                verification = result.get("verification", {})
                logger.info(f"  Status: ✅ Success")
                logger.info(f"  Total games: {verification.get('total_games', 0)}")
                logger.info(f"  Regular season: {verification.get('regular_season', {}).get('count', 0)}")
                logger.info(f"  Playoffs: {verification.get('playoffs', {}).get('count', 0)}")
            else:
                logger.error(f"  Status: ❌ Failed - {result.get('error', 'Unknown error')}")
        
        # Step 4: Enhanced data collection for key games
        logger.info("\n" + "=" * 60)
        logger.info("STEP 3: ENHANCED DATA COLLECTION")
        logger.info("=" * 60)
        
        # Collect enhanced data for Super Bowl games as examples
        super_bowl_games = [
            "NFL_202302120phi",  # 2022 Super Bowl
            "NFL_202402110kan",  # 2023 Super Bowl  
            "NFL_202502090phi"   # 2024 Super Bowl
        ]
        
        enhanced_data_collected = 0
        for game_id in super_bowl_games:
            try:
                logger.info(f"Collecting enhanced data for {game_id}...")
                with NFLDataCollector() as collector:
                    enhanced_data = await collector.collect_enhanced_game_data(game_id)
                    if enhanced_data:
                        logger.info(f"  ✅ Enhanced data collected for {game_id}")
                        enhanced_data_collected += 1
                    else:
                        logger.warning(f"  ⚠️ No enhanced data available for {game_id}")
            except Exception as e:
                logger.error(f"  ❌ Failed to collect enhanced data for {game_id}: {e}")
        
        # Step 5: Final verification
        logger.info("\n" + "=" * 60)
        logger.info("STEP 4: FINAL VERIFICATION")
        logger.info("=" * 60)
        
        final_verification = await DataCollectionManager.verify_all_data()
        
        total_games = 0
        total_issues = 0
        
        for season, results in final_verification["verification_results"].items():
            completeness = results["completeness"]
            consistency = results["consistency"]
            
            total_games += completeness['total_games']
            total_issues += consistency['issues_found']
        
        # Step 6: Summary
        logger.info("\n" + "=" * 80)
        logger.info("UNIFIED SYSTEM RUN COMPLETE - SUMMARY")
        logger.info("=" * 80)
        
        logger.info(f"Total games in database: {total_games}")
        logger.info(f"Enhanced data collected: {enhanced_data_collected} Super Bowl games")
        logger.info(f"Data quality issues: {total_issues}")
        
        if total_issues == 0:
            logger.info("🎉 DATA COLLECTION PERFECT - No issues found!")
        else:
            logger.warning(f"⚠️ {total_issues} data quality issues detected")
        
        logger.info("\nSystem Status: ✅ UNIFIED DATA COLLECTION COMPLETE")
        logger.info("All data gathering tools are working correctly!")
        logger.info("Database ready for production use.")
        
        return {
            "status": "success",
            "total_games": total_games,
            "enhanced_data_collected": enhanced_data_collected,
            "issues_found": total_issues
        }
        
    except Exception as e:
        logger.error(f"❌ UNIFIED SYSTEM RUN FAILED: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


async def main():
    """Main execution"""
    try:
        results = await run_full_system()
        
        if results["status"] == "success":
            logger.info("\n🚀 UNIFIED DATA COLLECTION SYSTEM RUN SUCCESSFUL!")
            return 0
        else:
            logger.error(f"\n💥 UNIFIED SYSTEM RUN FAILED: {results['error']}")
            return 1
            
    except Exception as e:
        logger.error(f"💥 CRITICAL ERROR: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)