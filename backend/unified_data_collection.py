#!/usr/bin/env python3
"""
Unified Data Collection Script
Integrates with the core FastAPI application to collect and verify NFL data
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
        logging.FileHandler("data_collection.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize database tables"""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully!")


async def collect_all_data():
    """Collect complete NFL data for 2022-2024 seasons"""
    logger.info("=== STARTING UNIFIED NFL DATA COLLECTION ===")
    
    # Initialize database
    init_database()
    
    # Collect data for all seasons
    seasons = [2022, 2023, 2024]
    results = await DataCollectionManager.collect_all_seasons(seasons, force_refresh=True)
    
    logger.info("=== DATA COLLECTION COMPLETE ===")
    
    # Print summary
    for season, result in results["results"].items():
        logger.info(f"Season {season}:")
        if result.get("status") == "completed":
            verification = result.get("verification", {})
            logger.info(f"  - Total games: {verification.get('total_games', 0)}")
            logger.info(f"  - Regular season: {verification.get('regular_season', {}).get('count', 0)}")
            logger.info(f"  - Playoffs: {verification.get('playoffs', {}).get('count', 0)}")
        else:
            logger.error(f"  - Failed: {result.get('error', 'Unknown error')}")
    
    return results


async def verify_data():
    """Verify data completeness and consistency"""
    logger.info("=== STARTING DATA VERIFICATION ===")
    
    verification_results = await DataCollectionManager.verify_all_data()
    
    for season, results in verification_results["verification_results"].items():
        logger.info(f"Season {season} Verification:")
        
        completeness = results["completeness"]
        logger.info(f"  - Total games: {completeness['total_games']}")
        logger.info(f"  - Regular season: {completeness['regular_season']['count']}/{completeness['regular_season']['expected']}")
        logger.info(f"  - Playoffs: {completeness['playoffs']['count']}/{completeness['playoffs']['expected']}")
        logger.info(f"  - Missing games: {completeness['missing_games']}")
        
        consistency = results["consistency"]
        logger.info(f"  - Data quality: {consistency['data_quality']}")
        if consistency["issues_found"] > 0:
            logger.warning(f"  - Issues found: {consistency['issues_found']}")
            for issue in consistency["issues"][:5]:  # Show first 5 issues
                logger.warning(f"    * {issue}")
    
    logger.info("=== DATA VERIFICATION COMPLETE ===")
    return verification_results


async def collect_missing_data():
    """Identify and collect missing data"""
    logger.info("=== IDENTIFYING AND COLLECTING MISSING DATA ===")
    
    # First verify what we have
    verification = await verify_data()
    
    # Collect missing data for each season
    for season in [2022, 2023, 2024]:
        logger.info(f"Checking season {season} for missing data...")
        
        with NFLDataCollector() as collector:
            completeness = await collector._verify_season_completeness(season)
            
            if completeness["missing_games"] > 0:
                logger.info(f"Found {completeness['missing_games']} missing games for {season}")
                logger.info("Attempting to collect missing data...")
                
                # Re-scrape the season to fill gaps
                await collector.collect_complete_season_data(season, force_refresh=True)
                
                # Verify again
                new_completeness = await collector._verify_season_completeness(season)
                logger.info(f"After re-collection: {new_completeness['missing_games']} games still missing")
            else:
                logger.info(f"Season {season} appears complete")


async def main():
    """Main execution function"""
    print("NFL Data Collection and Verification Tool")
    print("=" * 50)
    print("1. Collect all data (2022-2024)")
    print("2. Verify existing data")
    print("3. Identify and collect missing data")
    print("4. Full collection and verification")
    print("=" * 50)
    
    choice = input("Select option (1-4): ").strip()
    
    try:
        if choice == "1":
            await collect_all_data()
        elif choice == "2":
            await verify_data()
        elif choice == "3":
            await collect_missing_data()
        elif choice == "4":
            # Full workflow
            await collect_all_data()
            await verify_data()
            await collect_missing_data()
            await verify_data()  # Final verification
        else:
            print("Invalid option selected")
            return
            
        print("\n" + "=" * 50)
        print("Operation completed successfully!")
        print("Check 'data_collection.log' for detailed logs")
        
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())