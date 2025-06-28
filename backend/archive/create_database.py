#!/usr/bin/env python3
"""
Create database tables for NFL data aggregator
"""

import logging
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.core.database import engine
from app.models.sports import Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_tables():
    """Create all database tables"""
    logger.info("Creating database tables...")
    
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        return False


if __name__ == "__main__":
    success = create_tables()
    sys.exit(0 if success else 1)