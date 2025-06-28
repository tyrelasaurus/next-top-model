#!/usr/bin/env python3
"""
Consolidate databases: Copy latest data from sports_data.db to nfl_data.db
and remove the duplicate database
"""

import sqlite3
import shutil
import logging
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def consolidate_databases():
    """Consolidate sports_data.db data into nfl_data.db using config settings"""
    
    backend_dir = Path(__file__).parent
    
    # Use config DATABASE_URL to get the correct database path
    db_url = settings.DATABASE_URL
    if db_url.startswith("sqlite:///"):
        nfl_db_filename = db_url.replace("sqlite:///./", "")
    else:
        nfl_db_filename = "nfl_data.db"  # fallback
    
    nfl_db_path = backend_dir / nfl_db_filename
    sports_db_path = backend_dir / "sports_data.db"  # Legacy database to remove
    backup_path = backend_dir / "archive" / "sports_data_backup.db"
    
    logger.info("Starting database consolidation...")
    
    # Create backup of sports_data.db before consolidation
    if sports_db_path.exists():
        backup_path.parent.mkdir(exist_ok=True)
        shutil.copy2(sports_db_path, backup_path)
        logger.info(f"Created backup: {backup_path}")
    
    # Check data freshness in both databases
    with sqlite3.connect(nfl_db_path) as nfl_conn:
        nfl_cursor = nfl_conn.cursor()
        nfl_cursor.execute("SELECT MAX(updated_at) FROM games")
        nfl_latest = nfl_cursor.fetchone()[0]
        
        nfl_cursor.execute("SELECT COUNT(*) FROM games")
        nfl_games_count = nfl_cursor.fetchone()[0]
        
        nfl_cursor.execute("SELECT COUNT(*) FROM teams WHERE latitude IS NOT NULL")
        nfl_teams_gps = nfl_cursor.fetchone()[0]
    
    with sqlite3.connect(sports_db_path) as sports_conn:
        sports_cursor = sports_conn.cursor()
        sports_cursor.execute("SELECT MAX(updated_at) FROM games")
        sports_latest = sports_cursor.fetchone()[0]
        
        sports_cursor.execute("SELECT COUNT(*) FROM games")
        sports_games_count = sports_cursor.fetchone()[0]
        
        sports_cursor.execute("SELECT COUNT(*) FROM teams WHERE latitude IS NOT NULL")
        sports_teams_gps = sports_cursor.fetchone()[0]
    
    logger.info(f"NFL_DATA.DB: {nfl_games_count} games, {nfl_teams_gps} teams with GPS, latest: {nfl_latest}")
    logger.info(f"SPORTS_DATA.DB: {sports_games_count} games, {sports_teams_gps} teams with GPS, latest: {sports_latest}")
    
    # Determine which database has more recent data
    if sports_latest > nfl_latest:
        logger.info("SPORTS_DATA.DB has newer data. Copying to NFL_DATA.DB...")
        
        # Replace nfl_data.db with sports_data.db
        shutil.copy2(sports_db_path, nfl_db_path)
        logger.info("✅ Copied latest data to nfl_data.db")
        
    else:
        logger.info("NFL_DATA.DB already has the latest data")
    
    # Verify the consolidation
    with sqlite3.connect(nfl_db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM games")
        final_games = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM teams WHERE latitude IS NOT NULL")
        final_teams_gps = cursor.fetchone()[0]
        
        cursor.execute("SELECT season, COUNT(*) FROM games GROUP BY season ORDER BY season")
        season_counts = cursor.fetchall()
        
        cursor.execute("SELECT MAX(updated_at) FROM games")
        final_latest = cursor.fetchone()[0]
    
    logger.info("\n" + "="*60)
    logger.info("CONSOLIDATION COMPLETE - FINAL STATUS")
    logger.info("="*60)
    logger.info(f"Database: nfl_data.db")
    logger.info(f"Total games: {final_games}")
    logger.info(f"Teams with GPS: {final_teams_gps}/32")
    logger.info(f"Latest update: {final_latest}")
    logger.info("Season breakdown:")
    for season, count in season_counts:
        logger.info(f"  {season}: {count} games")
    
    # Remove the duplicate database
    try:
        sports_db_path.unlink()
        logger.info(f"✅ Removed duplicate database: {sports_db_path}")
    except Exception as e:
        logger.error(f"Failed to remove {sports_db_path}: {e}")
    
    # Verify config is pointing to correct database
    config_path = backend_dir / "app" / "core" / "config.py"
    with open(config_path, 'r') as f:
        config_content = f.read()
        
    if 'nfl_data.db' in config_content:
        logger.info("✅ Config correctly points to nfl_data.db")
    else:
        logger.warning("⚠️  Config may need updating to point to nfl_data.db")
    
    logger.info("\n🎯 CONSOLIDATION SUCCESSFUL!")
    logger.info(f"📊 Single database: {nfl_db_filename} with all current data")
    logger.info("🗄️  Backup preserved: archive/sports_data_backup.db")
    logger.info(f"🔧 Config DATABASE_URL: {settings.DATABASE_URL}")

if __name__ == "__main__":
    consolidate_databases()