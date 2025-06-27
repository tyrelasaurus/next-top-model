#!/usr/bin/env python3
"""Fix game times - store just dates when we don't have real kickoff times"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.core.database import SessionLocal
from backend.app.models import Game, League
import logging
from datetime import datetime, time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_game_times():
    """Fix game times to store just dates when we don't have real kickoff times"""
    db = SessionLocal()
    
    try:
        # Get all NFL games
        all_games = db.query(Game).filter(Game.league == League.NFL).all()
        logger.info(f"Total games to check: {len(all_games)}")
        
        midnight_games = 0
        updated_games = 0
        
        for game in all_games:
            if game.game_datetime:
                # Check if the time is midnight (00:00:00) - indicates we don't have real kickoff time
                if game.game_datetime.time() == time(0, 0, 0):
                    # Convert to just date at noon (12:00) to indicate "sometime during this day"
                    # This prevents the 00:00:00 fake timestamp while keeping a valid datetime
                    new_datetime = game.game_datetime.replace(hour=12, minute=0, second=0)
                    game.game_datetime = new_datetime
                    midnight_games += 1
                    updated_games += 1
        
        if updated_games > 0:
            db.commit()
            logger.info(f"Updated {updated_games} games from midnight timestamps to noon (indicating date-only)")
        
        # Verify the changes
        logger.info("\nVerifying game time distribution:")
        
        time_counts = {}
        for game in all_games:
            if game.game_datetime:
                time_str = game.game_datetime.strftime("%H:%M")
                time_counts[time_str] = time_counts.get(time_str, 0) + 1
        
        # Show top 5 most common times
        sorted_times = sorted(time_counts.items(), key=lambda x: x[1], reverse=True)
        logger.info("Most common game times:")
        for time_str, count in sorted_times[:5]:
            if time_str == "12:00":
                logger.info(f"  {time_str}: {count} games (date-only, no specific kickoff time)")
            else:
                logger.info(f"  {time_str}: {count} games")
                
        logger.info(f"\nTotal games with midnight timestamps converted: {midnight_games}")
        
    except Exception as e:
        logger.error(f"Error fixing game times: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    fix_game_times()