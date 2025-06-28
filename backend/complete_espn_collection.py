#!/usr/bin/env python3
"""
Complete ESPN Collection - Get to 100% coverage
Forces collection of all remaining games without stats
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from espn_overnight_stats_collector import OvernightStatsCollector
from app.core.database import SessionLocal
from app.models.sports import Game, TeamGameStat

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def force_complete_collection():
    """Force collection of all remaining games"""
    
    # First, clear the progress file to force reprocessing
    logger.info("Checking for games without statistics...")
    
    with SessionLocal() as db:
        # Get games without team stats
        games_without_stats = db.query(Game).filter(
            ~Game.game_uid.in_(
                db.query(TeamGameStat.game_uid).distinct()
            ),
            Game.season >= 2022,
            Game.game_datetime.isnot(None)
        ).all()
        
        total_remaining = len(games_without_stats)
        logger.info(f"Found {total_remaining} games without statistics")
        
        if total_remaining == 0:
            logger.info("✅ Already at 100% coverage!")
            return 0
    
    # Create collector and manually set processed games
    async with OvernightStatsCollector() as collector:
        # Load existing progress
        collector.load_progress()
        
        # Mark all games with stats as processed
        with SessionLocal() as db:
            games_with_stats = db.query(TeamGameStat.game_uid).distinct().all()
            for (game_uid,) in games_with_stats:
                collector.processed_games.add(game_uid)
        
        logger.info(f"Marked {len(collector.processed_games)} games as already processed")
        logger.info("Starting collection of remaining games...")
        
        # Run collection
        await collector.run_overnight_collection()
    
    return 0

async def main():
    logger.info("=" * 80)
    logger.info("COMPLETING ESPN COLLECTION TO 100%")
    logger.info("=" * 80)
    
    try:
        exit_code = await force_complete_collection()
        
        # Final status check
        with SessionLocal() as db:
            total_games = db.query(Game).filter(Game.season >= 2022).count()
            games_with_stats = db.query(Game).join(TeamGameStat).distinct().count()
            coverage = games_with_stats / total_games * 100
            
            logger.info(f"\n📊 FINAL COVERAGE: {games_with_stats}/{total_games} games ({coverage:.1f}%)")
            
            if coverage >= 99.5:
                logger.info("✅ SUCCESSFULLY ACHIEVED ~100% COVERAGE!")
            else:
                logger.info(f"⚠️  Still need to process {total_games - games_with_stats} games")
        
        return exit_code
        
    except Exception as e:
        logger.error(f"❌ Collection failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)