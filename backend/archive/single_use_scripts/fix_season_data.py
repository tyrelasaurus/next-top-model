#!/usr/bin/env python3
"""Fix season data and properly categorize playoff games"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.core.database import SessionLocal
from backend.app.models import Game, League
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_season_data():
    """Fix season data and properly categorize games"""
    db = SessionLocal()
    
    try:
        # Get all NFL games
        all_games = db.query(Game).filter(Game.league == League.NFL).all()
        logger.info(f"Total games: {len(all_games)}")
        
        # Categorize games by actual season and type
        updates_made = 0
        
        for game in all_games:
            if not game.game_datetime:
                continue
                
            game_date = game.game_datetime.date()
            original_week = game.week
            
            # Determine proper game type and week based on date and current week
            if game.season == 2024 and game_date >= datetime(2025, 1, 1).date():
                # These are 2024 season playoffs in early 2025
                if game_date.month == 1:
                    if game_date.day <= 6:  # Week 18 (final regular season)
                        game.game_type = "regular"
                        game.week = 18
                    elif game_date.day <= 13:  # Wild Card weekend
                        game.game_type = "wildcard"
                        game.week = 19
                    elif game_date.day <= 20:  # Divisional round
                        game.game_type = "divisional" 
                        game.week = 20
                    elif game_date.day <= 27:  # Conference championships
                        game.game_type = "conference"
                        game.week = 21
                elif game_date.month == 2 and game_date.day <= 15:  # Super Bowl
                    game.game_type = "superbowl"
                    game.week = 22
                
                if original_week != game.week or not game.game_type:
                    logger.info(f"Updated {game.game_uid}: Week {original_week} -> {game.week}, Type: {game.game_type}")
                    updates_made += 1
                    
            else:
                # Regular season games
                if not game.game_type and game.week and game.week <= 18:
                    game.game_type = "regular"
                    updates_made += 1
        
        # Commit updates
        if updates_made > 0:
            db.commit()
            logger.info(f"Updated {updates_made} games with proper game types and weeks")
        
        # Verify the data
        logger.info("\n=== FINAL GAME BREAKDOWN ===")
        
        # Count by season and type
        for season in [2022, 2023, 2024]:
            season_games = db.query(Game).filter(
                Game.league == League.NFL,
                Game.season == season
            ).all()
            
            if not season_games:
                continue
                
            regular = len([g for g in season_games if g.game_type == "regular"])
            wildcard = len([g for g in season_games if g.game_type == "wildcard"])
            divisional = len([g for g in season_games if g.game_type == "divisional"])
            conference = len([g for g in season_games if g.game_type == "conference"])
            superbowl = len([g for g in season_games if g.game_type == "superbowl"])
            
            dates = [g.game_datetime for g in season_games if g.game_datetime]
            date_range = f"{min(dates).date()} to {max(dates).date()}" if dates else "No dates"
            
            logger.info(f"\n{season} Season ({len(season_games)} total games):")
            logger.info(f"  Regular: {regular} games")
            if wildcard > 0:
                logger.info(f"  Wild Card: {wildcard} games")
            if divisional > 0:
                logger.info(f"  Divisional: {divisional} games")
            if conference > 0:
                logger.info(f"  Conference: {conference} games")
            if superbowl > 0:
                logger.info(f"  Super Bowl: {superbowl} games")
            logger.info(f"  Date range: {date_range}")
        
        # Verify no future games
        future_games = db.query(Game).filter(
            Game.league == League.NFL,
            Game.game_datetime > datetime(2025, 6, 27)  # Current date
        ).all()
        
        if future_games:
            logger.warning(f"WARNING: Found {len(future_games)} games with future dates:")
            for game in future_games[:5]:  # Show first 5
                logger.warning(f"  {game.game_uid}: {game.game_datetime}")
        else:
            logger.info(f"\n✅ No future games found - all data is historical as of June 27, 2025")
            
    except Exception as e:
        logger.error(f"Error fixing season data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    fix_season_data()