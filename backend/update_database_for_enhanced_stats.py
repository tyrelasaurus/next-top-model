#!/usr/bin/env python3
"""
Update database schema for enhanced statistics collection
Add TeamGameStat and TeamSeasonStat tables
"""

import sys
import logging
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.core.database import engine, Base
from app.models.sports import Team, Game, Player, PlayerStat, TeamGameStat, TeamSeasonStat

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_database_schema():
    """Create new tables for enhanced statistics"""
    
    logger.info("Updating database schema for enhanced statistics...")
    
    try:
        # Create all tables (existing ones will be skipped)
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ Database schema updated successfully!")
        logger.info("New tables added:")
        logger.info("  📊 team_game_stats - Individual game statistics for teams")
        logger.info("  📈 team_season_stats - Season-long team performance metrics")
        
        # Verify tables exist
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        required_tables = ['team_game_stats', 'team_season_stats']
        for table in required_tables:
            if table in tables:
                logger.info(f"  ✅ {table} table created successfully")
            else:
                logger.error(f"  ❌ {table} table not found")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database schema update failed: {e}")
        return False

if __name__ == "__main__":
    success = update_database_schema()
    sys.exit(0 if success else 1)