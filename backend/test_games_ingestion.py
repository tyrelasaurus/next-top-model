#!/usr/bin/env python3
"""Test script to ingest recent NFL games"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.ingestion.thesportsdb import TheSportsDBClient
from backend.app.models import Game, League
from backend.app.core.database import SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ingest_recent_nfl_games():
    """Ingest recent NFL games"""
    client = TheSportsDBClient()
    db = SessionLocal()
    
    try:
        # Get recent NFL games using the previous events endpoint
        logger.info("Fetching recent NFL games from TheSportsDB...")
        schedule_data = client.get_schedule("4391", "2024")  # Will fallback to previous events
        logger.info(f"Found {len(schedule_data)} games")
        
        added_count = 0
        updated_count = 0
        
        # Transform and save each game
        for tsdb_event in schedule_data[:10]:  # Limit to first 10 for testing
            try:
                game_data = client.transform_game_data(tsdb_event, League.NFL)
                
                logger.info(f"Processing game: {tsdb_event.get('strEvent', 'Unknown')} - Season: {game_data.get('season')}")
                
                # Check if game already exists
                existing_game = db.query(Game).filter(Game.game_uid == game_data["game_uid"]).first()
                if existing_game:
                    # Update existing game
                    for field, value in game_data.items():
                        if field not in ['game_uid', 'created_at']:
                            setattr(existing_game, field, value)
                    updated_count += 1
                    logger.info(f"Updated game: {existing_game.game_uid}")
                else:
                    # Create new game
                    game = Game(**game_data)
                    db.add(game)
                    added_count += 1
                    logger.info(f"Added game: {game.game_uid}")
                    
            except Exception as e:
                logger.warning(f"Error processing game {tsdb_event.get('idEvent', 'unknown')}: {e}")
                continue
        
        db.commit()
        logger.info(f"Games ingestion completed! Added: {added_count}, Updated: {updated_count}")
        
        # Query and display games
        games = db.query(Game).filter(Game.league == League.NFL).all()
        logger.info(f"\nTotal NFL games in database: {len(games)}")
        for game in games[:5]:  # Show first 5
            home_team = game.home_team_uid.split('_')[1] if game.home_team_uid else 'Unknown'
            away_team = game.away_team_uid.split('_')[1] if game.away_team_uid else 'Unknown'
            logger.info(f"  - {game.season} S{game.season} W{game.week}: {away_team} @ {home_team} ({game.game_uid})")
            
    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        db.rollback()
        raise
    finally:
        client.close()
        db.close()


if __name__ == "__main__":
    ingest_recent_nfl_games()