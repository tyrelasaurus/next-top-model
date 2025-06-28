#!/usr/bin/env python3
"""Clean duplicate games and inconsistent data sources"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.core.database import SessionLocal
from backend.app.models import Game, League
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_duplicate_games():
    """Remove duplicate games and clean data source conflicts"""
    db = SessionLocal()
    
    try:
        # Get all NFL games
        all_games = db.query(Game).filter(Game.league == League.NFL).all()
        logger.info(f"Total games before cleanup: {len(all_games)}")
        
        # Separate by source
        thesportsdb_games = [g for g in all_games if g.source == 'thesportsdb']
        pfr_games = [g for g in all_games if g.source == 'pro_football_reference']
        
        logger.info(f"TheSportsDB games: {len(thesportsdb_games)}")
        logger.info(f"Pro Football Reference games: {len(pfr_games)}")
        
        # Find duplicates based on teams and similar dates
        duplicates_to_remove = []
        
        for tsdb_game in thesportsdb_games:
            if not tsdb_game.home_team or not tsdb_game.away_team:
                continue
                
            # Look for matching PFR game with same teams
            for pfr_game in pfr_games:
                if (pfr_game.home_team and pfr_game.away_team and
                    pfr_game.home_team.name == tsdb_game.home_team.name and
                    pfr_game.away_team.name == tsdb_game.away_team.name):
                    
                    logger.info(f"DUPLICATE FOUND - Removing TheSportsDB version:")
                    logger.info(f"  TheSportsDB: {tsdb_game.game_uid} - {tsdb_game.game_datetime}")
                    logger.info(f"  PFR: {pfr_game.game_uid} - {pfr_game.game_datetime}")
                    
                    duplicates_to_remove.append(tsdb_game)
                    break
        
        # Remove TheSportsDB duplicates
        for game in duplicates_to_remove:
            db.delete(game)
            
        # Also remove any TheSportsDB games with future dates (clearly incorrect)
        future_games = [g for g in thesportsdb_games 
                       if g.game_datetime and g.game_datetime.year > 2024]
        
        for game in future_games:
            if game not in duplicates_to_remove:  # Don't double-delete
                logger.info(f"Removing future-dated game: {game.game_uid} - {game.game_datetime}")
                db.delete(game)
                duplicates_to_remove.append(game)
        
        # Commit changes
        db.commit()
        
        logger.info(f"Removed {len(duplicates_to_remove)} duplicate/incorrect games")
        
        # Final count
        final_games = db.query(Game).filter(Game.league == League.NFL).all()
        logger.info(f"Total games after cleanup: {len(final_games)}")
        
        # Verify data sources
        sources = {}
        for game in final_games:
            source = game.source or 'unknown'
            sources[source] = sources.get(source, 0) + 1
            
        logger.info("Final data sources:")
        for source, count in sources.items():
            logger.info(f"  {source}: {count} games")
            
        # Verify no more duplicates
        games_by_teams = {}
        remaining_duplicates = 0
        
        for game in final_games:
            if game.home_team and game.away_team and game.game_datetime:
                key = f"{game.home_team.name}_{game.away_team.name}_{game.game_datetime.date()}"
                if key in games_by_teams:
                    remaining_duplicates += 1
                    logger.warning(f"Still duplicate: {key}")
                else:
                    games_by_teams[key] = game
                    
        logger.info(f"Remaining duplicates: {remaining_duplicates}")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    clean_duplicate_games()