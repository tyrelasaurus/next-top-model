#!/usr/bin/env python3
"""
Test script for the unified data collection system
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.services.data_collector import NFLDataCollector, DataCollectionManager
from app.core.database import engine, SessionLocal
from app.models.sports import Base, Game, Team

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_data_verification():
    """Test the data verification system"""
    logger.info("Testing data verification system...")
    
    # Initialize database
    Base.metadata.create_all(bind=engine)
    
    # Check existing data
    db = SessionLocal()
    try:
        total_games = db.query(Game).count()
        total_teams = db.query(Team).count()
        
        logger.info(f"Current database status:")
        logger.info(f"  - Teams: {total_teams}")
        logger.info(f"  - Games: {total_games}")
        
        # Test verification for each season
        for season in [2022, 2023, 2024]:
            season_games = db.query(Game).filter(Game.season == season).count()
            logger.info(f"  - {season} season: {season_games} games")
        
        # Test the verification service
        verification_results = await DataCollectionManager.verify_all_data()
        logger.info("Verification service test completed successfully")
        
        return verification_results
        
    finally:
        db.close()


async def test_single_season_collection():
    """Test collecting data for a single season"""
    logger.info("Testing single season data collection...")
    
    # Test with 2024 season (most recent)
    with NFLDataCollector() as collector:
        results = await collector.collect_complete_season_data(2024, force_refresh=False)
        
        logger.info(f"Collection results: {results['status']}")
        if results.get('verification'):
            verification = results['verification']
            logger.info(f"Total games collected: {verification.get('total_games', 0)}")
        
        return results


async def test_missing_games_detection():
    """Test missing games detection"""
    logger.info("Testing missing games detection...")
    
    db = SessionLocal()
    try:
        for season in [2022, 2023, 2024]:
            games = db.query(Game).filter(Game.season == season).all()
            
            # Count by game type
            game_types = {}
            for game in games:
                game_type = game.game_type or 'regular'
                game_types[game_type] = game_types.get(game_type, 0) + 1
            
            logger.info(f"Season {season} game breakdown:")
            for game_type, count in game_types.items():
                logger.info(f"  - {game_type}: {count}")
            
            # Check for missing playoff games
            playoff_count = sum(game_types.get(t, 0) for t in ['wildcard', 'divisional', 'conference', 'superbowl'])
            if playoff_count < 13:
                logger.warning(f"Season {season} missing playoff games: {13 - playoff_count}")
            else:
                logger.info(f"Season {season} playoff games complete")
                
    finally:
        db.close()


async def main():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("UNIFIED DATA COLLECTION SYSTEM TEST")
    logger.info("=" * 60)
    
    try:
        # Test 1: Data verification
        await test_data_verification()
        logger.info("✅ Data verification test passed")
        
        # Test 2: Missing games detection
        await test_missing_games_detection()
        logger.info("✅ Missing games detection test passed")
        
        # Test 3: Single season collection (optional)
        print("\nWould you like to test data collection? (y/n): ", end="")
        if input().lower().startswith('y'):
            await test_single_season_collection()
            logger.info("✅ Single season collection test passed")
        
        logger.info("=" * 60)
        logger.info("ALL TESTS COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())