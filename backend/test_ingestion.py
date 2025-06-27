#!/usr/bin/env python3
"""Test script to ingest NFL team data from TheSportsDB"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.ingestion.thesportsdb import TheSportsDBClient
from backend.app.models import Team, League
from backend.app.core.database import SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_team_ingestion():
    """Test ingesting NFL teams"""
    client = TheSportsDBClient()
    db = SessionLocal()
    
    try:
        # Get NFL teams
        logger.info("Fetching NFL teams from TheSportsDB...")
        teams_data = client.get_all_teams("NFL")
        logger.info(f"Found {len(teams_data)} teams")
        
        # Transform and save each team
        for tsdb_team in teams_data[:5]:  # Just first 5 for testing
            team_data = client.transform_team_data(tsdb_team, League.NFL)
            
            # Check if team already exists
            existing_team = db.query(Team).filter(Team.team_uid == team_data["team_uid"]).first()
            if existing_team:
                logger.info(f"Team {team_data['name']} already exists")
                continue
            
            # Create new team
            team = Team(**team_data)
            db.add(team)
            logger.info(f"Added team: {team.name}")
        
        db.commit()
        logger.info("Team ingestion completed successfully!")
        
        # Query and display teams
        teams = db.query(Team).filter(Team.league == League.NFL).all()
        logger.info(f"\nTotal NFL teams in database: {len(teams)}")
        for team in teams:
            logger.info(f"  - {team.city} {team.name} (ID: {team.team_uid})")
            
    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        db.rollback()
        raise
    finally:
        client.close()
        db.close()


if __name__ == "__main__":
    test_team_ingestion()