#!/usr/bin/env python3
"""
Clean up backend directory - archive obsolete files and organize structure
"""

import os
import shutil
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_backend():
    """Clean up backend directory"""
    logger.info("Starting backend cleanup...")
    
    backend_dir = Path("/Volumes/Extreme SSD/next_top_model/backend")
    archive_dir = backend_dir / "archive"
    
    # Create archive directory
    archive_dir.mkdir(exist_ok=True)
    
    # Files to archive (obsolete scripts)
    files_to_archive = [
        "augment_with_pfr_data.py",  # Replaced by incremental version
        "pfr_detailed_augmentation.py",  # Replaced by incremental version
        "collect_nfl_seasons.py",  # Keep for now but may archive later
        "populate_nfl_teams.py",  # Replaced by direct SQL version
        "fix_teams_gps.py",  # One-time use script
        "create_database.py",  # One-time use script
    ]
    
    # Keep these core files
    core_files = [
        "incremental_pfr_augmentation.py",  # New efficient version
        "populate_teams.py",  # Core team population
        "run_thesportsdb_system.py",  # Core data collection
        "run_unified_system.py",  # Unified approach
        "nfl_data.db",  # Database
        "server.log",  # Logs
    ]
    
    archived_count = 0
    
    # Archive obsolete files
    for file_name in files_to_archive:
        file_path = backend_dir / file_name
        if file_path.exists():
            archive_path = archive_dir / file_name
            try:
                shutil.move(str(file_path), str(archive_path))
                logger.info(f"Archived: {file_name}")
                archived_count += 1
            except Exception as e:
                logger.error(f"Failed to archive {file_name}: {e}")
    
    # Clean up logs and temporary files
    temp_files = [
        "*.log",
        "*.tmp", 
        "__pycache__",
        "*.pyc"
    ]
    
    for pattern in temp_files:
        if pattern == "__pycache__":
            # Remove __pycache__ directories
            for pycache_dir in backend_dir.rglob("__pycache__"):
                try:
                    shutil.rmtree(pycache_dir)
                    logger.info(f"Removed: {pycache_dir}")
                except Exception as e:
                    logger.error(f"Failed to remove {pycache_dir}: {e}")
        else:
            # Remove files matching pattern
            for file_path in backend_dir.glob(pattern):
                if file_path.name != "server.log":  # Keep main server log
                    try:
                        file_path.unlink()
                        logger.info(f"Removed: {file_path.name}")
                    except Exception as e:
                        logger.error(f"Failed to remove {file_path.name}: {e}")
    
    logger.info(f"Cleanup complete. Archived {archived_count} files.")
    
    # Show current structure
    logger.info("\nCurrent backend structure:")
    for item in sorted(backend_dir.iterdir()):
        if item.is_file():
            size = item.stat().st_size
            if size > 1024*1024:  # > 1MB
                size_str = f"{size / (1024*1024):.1f}MB"
            elif size > 1024:  # > 1KB
                size_str = f"{size / 1024:.1f}KB"
            else:
                size_str = f"{size}B"
            logger.info(f"  📄 {item.name} ({size_str})")
        elif item.is_dir() and not item.name.startswith('.'):
            logger.info(f"  📁 {item.name}/")

if __name__ == "__main__":
    cleanup_backend()