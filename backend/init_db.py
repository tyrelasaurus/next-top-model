#!/usr/bin/env python3
"""Initialize database tables"""

import sys
from pathlib import Path

# Add parent directory to path so we can import our app
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.core.database import engine
from backend.app.models import Base

def init_db():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()