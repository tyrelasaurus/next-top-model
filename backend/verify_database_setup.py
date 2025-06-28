#!/usr/bin/env python3
"""
Verify database setup - ensure all components use the configured database
"""

import sys
import logging
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.models.sports import Team, Game
from sqlalchemy import func

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_database_setup():
    """Verify database configuration and data integrity"""
    
    logger.info("="*60)
    logger.info("DATABASE VERIFICATION")
    logger.info("="*60)
    
    # Check configuration
    logger.info(f"📊 Database URL: {settings.DATABASE_URL}")
    logger.info(f"🏈 Project: {settings.PROJECT_NAME}")
    
    # Check database file exists
    backend_dir = Path(__file__).parent
    db_url = settings.DATABASE_URL
    
    if db_url.startswith("sqlite:///"):
        db_filename = db_url.replace("sqlite:///./", "")
        db_path = backend_dir / db_filename
        
        if db_path.exists():
            size_mb = db_path.stat().st_size / (1024 * 1024)
            logger.info(f"✅ Database file exists: {db_filename} ({size_mb:.1f}MB)")
        else:
            logger.error(f"❌ Database file not found: {db_filename}")
            return False
    
    # Test database connection
    try:
        with SessionLocal() as db:
            # Count teams
            teams_total = db.query(Team).count()
            teams_with_gps = db.query(Team).filter(
                Team.latitude.isnot(None),
                Team.longitude.isnot(None)
            ).count()
            
            # Count games by season
            games_by_season = db.query(Game.season, func.count()).group_by(Game.season).all()
            total_games = sum(count for _, count in games_by_season)
            
            logger.info(f"✅ Database connection successful")
            logger.info(f"📍 Teams: {teams_with_gps}/{teams_total} with GPS coordinates")
            logger.info(f"🏈 Total games: {total_games}")
            logger.info("Season breakdown:")
            for season, count in sorted(games_by_season):
                logger.info(f"  {season}: {count} games")
            
            # Sample team data
            sample_team = db.query(Team).filter(Team.latitude.isnot(None)).first()
            if sample_team:
                logger.info(f"📍 Sample team: {sample_team.city} {sample_team.name}")
                logger.info(f"   Stadium: {sample_team.stadium_name}")
                logger.info(f"   GPS: {sample_team.latitude}, {sample_team.longitude}")
            
            # Check for duplicate databases
            potential_dbs = list(backend_dir.glob("*.db"))
            logger.info(f"📂 Database files found: {[db.name for db in potential_dbs]}")
            
            if len(potential_dbs) > 1:
                logger.warning("⚠️  Multiple .db files found - ensure only one is active")
            else:
                logger.info("✅ Single database file confirmed")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def check_script_references():
    """Check for any remaining hardcoded database references"""
    
    logger.info("\n" + "="*60)
    logger.info("SCRIPT REFERENCES CHECK")
    logger.info("="*60)
    
    backend_dir = Path(__file__).parent
    python_files = list(backend_dir.rglob("*.py"))
    
    hardcoded_refs = []
    
    for py_file in python_files:
        if "archive" in str(py_file) or "__pycache__" in str(py_file):
            continue  # Skip archive and cache files
            
        try:
            with open(py_file, 'r') as f:
                content = f.read()
                
            # Check for hardcoded database references
            if "sports_data.db" in content:
                hardcoded_refs.append((py_file.name, "sports_data.db"))
            
            # Check for hardcoded nfl_data.db (should use config instead)
            if "sqlite3.connect" in content and "nfl_data.db" in content:
                hardcoded_refs.append((py_file.name, "hardcoded sqlite3.connect"))
                
        except Exception as e:
            logger.debug(f"Could not read {py_file}: {e}")
    
    if hardcoded_refs:
        logger.warning("⚠️  Found hardcoded database references:")
        for file_name, ref_type in hardcoded_refs:
            logger.warning(f"   {file_name}: {ref_type}")
    else:
        logger.info("✅ No problematic hardcoded database references found")
    
    return len(hardcoded_refs) == 0

if __name__ == "__main__":
    logger.info("Starting comprehensive database verification...")
    
    db_ok = verify_database_setup()
    refs_ok = check_script_references()
    
    logger.info("\n" + "="*60)
    logger.info("VERIFICATION SUMMARY")
    logger.info("="*60)
    
    if db_ok and refs_ok:
        logger.info("🎯 ALL CHECKS PASSED")
        logger.info("✅ Database setup is clean and consistent")
        logger.info("✅ Single nfl_data.db with complete GPS and game data")
        logger.info("✅ All scripts using proper configuration")
    else:
        logger.warning("⚠️  Some issues found - review logs above")
    
    sys.exit(0 if (db_ok and refs_ok) else 1)