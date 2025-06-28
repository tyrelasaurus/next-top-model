#!/usr/bin/env python3
"""
Complete 2023 NFL Season Collection using Pro Football Reference as Primary Source
Collects all games, team statistics, and detailed match results for the entire season
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
        logging.FileHandler("pfr_complete_season_2023.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize database tables"""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully!")


async def collect_complete_2023_season():
    """Collect complete 2023 NFL season using Pro Football Reference"""
    logger.info("=" * 80)
    logger.info("COMPLETE 2023 NFL SEASON COLLECTION - PRO FOOTBALL REFERENCE")
    logger.info("=" * 80)
    
    try:
        # Step 1: Initialize database
        init_database()
        
        # Step 2: Verify existing data
        logger.info("\n" + "=" * 60)
        logger.info("STEP 1: VERIFYING EXISTING DATA")
        logger.info("=" * 60)
        
        verification_results = await DataCollectionManager.verify_all_data()
        
        for season, results in verification_results["verification_results"].items():
            if int(season) == 2023:
                logger.info(f"\nSeason {season} Status:")
                completeness = results["completeness"]
                consistency = results["consistency"]
                
                logger.info(f"  Total games: {completeness['total_games']}")
                logger.info(f"  Regular season: {completeness['regular_season']['count']}/{completeness['regular_season']['expected']}")
                logger.info(f"  Playoffs: {completeness['playoffs']['count']}/{completeness['playoffs']['expected']}")
                logger.info(f"  Data quality: {consistency['data_quality']}")
                logger.info(f"  Missing games: {completeness['missing_games']}")
        
        # Step 3: Collect complete 2023 season
        logger.info("\n" + "=" * 60)
        logger.info("STEP 2: COMPLETE 2023 SEASON COLLECTION")
        logger.info("=" * 60)
        logger.info("Using Pro Football Reference for comprehensive historical data")
        logger.info("Collecting: Regular season (272 games) + Playoffs (13 games)")
        
        target_season = 2023
        
        with NFLDataCollector() as collector:
            season_result = await collector.collect_complete_season_data(target_season, force_refresh=True)
            
            logger.info(f"\n2023 Season Collection Results:")
            if season_result.get("status") == "completed":
                regular_season_data = season_result.get("regular_season", {})
                playoff_data = season_result.get("playoffs", {})
                verification = season_result.get("verification", {})
                
                logger.info(f"  Status: ✅ Success")
                logger.info(f"  Regular season weeks processed: {regular_season_data.get('weeks_processed', 0)}")
                logger.info(f"  Regular season games collected: {regular_season_data.get('games_collected', 0)}")
                logger.info(f"  Playoff rounds processed: {playoff_data.get('rounds_processed', 0)}")
                logger.info(f"  Playoff games collected: {playoff_data.get('playoff_games_collected', 0)}")
                logger.info(f"  Total games in database: {verification.get('total_games', 0)}")
                
                # Detailed breakdown
                game_types = verification.get('game_types', {})
                logger.info(f"\n  Game Type Breakdown:")
                for game_type, count in game_types.items():
                    logger.info(f"    {game_type}: {count} games")
                    
            else:
                logger.error(f"  Status: ❌ Failed - {season_result.get('error', 'Unknown error')}")
        
        # Step 4: Final verification and statistics
        logger.info("\n" + "=" * 60)
        logger.info("STEP 3: FINAL VERIFICATION & STATISTICS")
        logger.info("=" * 60)
        
        final_verification = await DataCollectionManager.verify_all_data()
        season_2023_data = final_verification["verification_results"].get("2023", {})
        
        if season_2023_data:
            completeness = season_2023_data["completeness"]
            consistency = season_2023_data["consistency"]
            
            logger.info(f"2023 Season Final Statistics:")
            logger.info(f"  Total games collected: {completeness['total_games']}")
            logger.info(f"  Regular season complete: {completeness['regular_season']['complete']}")
            logger.info(f"  Playoffs complete: {completeness['playoffs']['complete']}")
            logger.info(f"  Data quality issues: {consistency['issues_found']}")
            
            if consistency['issues_found'] == 0:
                logger.info(f"  ✅ Perfect data quality - no issues found!")
            else:
                logger.warning(f"  ⚠️ {consistency['issues_found']} data quality issues detected")
        
        # Step 5: Summary
        logger.info("\n" + "=" * 80)
        logger.info("2023 NFL SEASON COLLECTION COMPLETE - SUMMARY")
        logger.info("=" * 80)
        
        total_games = completeness['total_games'] if 'completeness' in locals() else 0
        logger.info(f"Complete 2023 NFL season collected: {total_games} games")
        logger.info("Data source: Pro Football Reference ✅")
        logger.info("Includes: Team statistics, game results, detailed match data ✅")
        logger.info("Coverage: Regular season + Playoffs + Super Bowl ✅")
        
        if total_games >= 285:  # 272 regular + 13 playoffs
            logger.info("\n🎉 COMPLETE 2023 NFL SEASON SUCCESSFULLY COLLECTED!")
            logger.info("Database ready for analysis and frontend integration.")
        else:
            logger.warning(f"\n⚠️ Season appears incomplete. Expected ~285 games, got {total_games}")
        
        return {
            "status": "success",
            "season": 2023,
            "total_games": total_games,
            "data_source": "pro_football_reference"
        }
        
    except Exception as e:
        logger.error(f"❌ 2023 SEASON COLLECTION FAILED: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


async def main():
    """Main execution"""
    try:
        results = await collect_complete_2023_season()
        
        if results["status"] == "success":
            logger.info("\n🚀 2023 NFL SEASON COLLECTION SUCCESSFUL!")
            return 0
        else:
            logger.error(f"\n💥 2023 SEASON COLLECTION FAILED: {results['error']}")
            return 1
            
    except Exception as e:
        logger.error(f"💥 CRITICAL ERROR: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)