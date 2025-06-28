#!/usr/bin/env python3
"""Clear all data from the database"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.models import Team, Game, Player, PlayerStat
from backend.app.core.database import SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clear_database():
    """Clear all data from database tables"""
    db = SessionLocal()
    
    try:
        # Delete in order to respect foreign key constraints
        logger.info("Clearing player stats...")
        db.query(PlayerStat).delete()
        
        logger.info("Clearing players...")
        db.query(Player).delete()
        
        logger.info("Clearing games...")
        db.query(Game).delete()
        
        logger.info("Clearing teams...")
        db.query(Team).delete()
        
        db.commit()
        logger.info("Database cleared successfully!")
        
    except Exception as e:
        logger.error(f"Error clearing database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    clear_database()