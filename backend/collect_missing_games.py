#!/usr/bin/env python3
"""
Collect Missing Games - Target only games without statistics
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from espn_overnight_stats_collector import OvernightStatsCollector
from app.core.database import SessionLocal
from app.models.sports import Game, Team, TeamGameStat

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def collect_only_missing_games():
    """Collect only games that don't have team statistics"""
    
    # Get list of games without stats
    games_to_process = []
    
    with SessionLocal() as db:
        # Get games without team stats
        games_without_stats = db.query(Game).filter(
            ~Game.game_uid.in_(
                db.query(TeamGameStat.game_uid).distinct()
            ),
            Game.season >= 2022,
            Game.game_datetime.isnot(None)
        ).all()
        
        games_to_process = [(g.game_uid, g.game_datetime, g.home_team_uid, g.away_team_uid) 
                           for g in games_without_stats]
        
        logger.info(f"Found {len(games_to_process)} games without statistics")
    
    if not games_to_process:
        logger.info("✅ Already at 100% coverage!")
        return 0
    
    # Process these specific games
    async with OvernightStatsCollector() as collector:
        # Don't load previous progress - start fresh
        collector.processed_games = set()
        collector.failed_games = set()
        
        processed_count = 0
        
        for game_uid, game_datetime, home_uid, away_uid in games_to_process:
            try:
                with SessionLocal() as db:
                    game = db.query(Game).filter(Game.game_uid == game_uid).first()
                    if not game:
                        continue
                    
                    home_team = db.query(Team).filter(Team.team_uid == home_uid).first()
                    away_team = db.query(Team).filter(Team.team_uid == away_uid).first()
                    
                    if not home_team or not away_team:
                        continue
                    
                    logger.info(f"Processing: {away_team.city} {away_team.name} @ {home_team.city} {home_team.name} ({game_datetime.date()})")
                    
                    # Find ESPN game ID
                    espn_game_id = await collector.find_espn_game_id(game)
                    
                    if espn_game_id:
                        # Collect team game stats
                        stats_added = await collector.collect_team_game_stats(game, espn_game_id)
                        
                        if stats_added > 0:
                            processed_count += 1
                            logger.info(f"  ✅ Added {stats_added} team statistics")
                        else:
                            logger.warning(f"  ⚠️  No statistics added")
                    else:
                        logger.warning(f"  ❌ ESPN game not found")
                
                # Save progress every 10 games
                if processed_count % 10 == 0 and processed_count > 0:
                    logger.info(f"Progress: {processed_count} games processed")
                    
            except Exception as e:
                logger.error(f"Error processing game {game_uid}: {e}")
                continue
        
        logger.info(f"\nTotal games processed: {processed_count}")
    
    return 0

async def main():
    logger.info("=" * 80)
    logger.info("COLLECTING MISSING GAMES FOR 100% COVERAGE")
    logger.info("=" * 80)
    
    try:
        exit_code = await collect_only_missing_games()
        
        # Final status check
        with SessionLocal() as db:
            total_games = db.query(Game).filter(Game.season >= 2022).count()
            games_with_stats = db.query(Game).join(TeamGameStat).distinct().count()
            coverage = games_with_stats / total_games * 100
            
            logger.info(f"\n📊 FINAL COVERAGE: {games_with_stats}/{total_games} games ({coverage:.1f}%)")
            
            if coverage >= 99.5:
                logger.info("✅ SUCCESSFULLY ACHIEVED ~100% COVERAGE!")
            else:
                remaining = total_games - games_with_stats
                logger.info(f"⚠️  Still need to process {remaining} games")
                logger.info("These games may not be available in ESPN's API")
        
        return exit_code
        
    except Exception as e:
        logger.error(f"❌ Collection failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)