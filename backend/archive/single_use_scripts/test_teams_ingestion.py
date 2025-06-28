#!/usr/bin/env python3
"""Test script to ingest all NFL teams"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.ingestion.thesportsdb import TheSportsDBClient
from backend.app.models import Team, League
from backend.app.core.database import SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ingest_all_nfl_teams():
    """Ingest all NFL teams"""
    client = TheSportsDBClient()
    db = SessionLocal()
    
    try:
        # Get all NFL teams
        logger.info("Fetching all NFL teams from TheSportsDB...")
        teams_data = client.get_all_teams("NFL")
        logger.info(f"Found {len(teams_data)} teams")
        
        added_count = 0
        updated_count = 0
        
        # Transform and save each team
        for tsdb_team in teams_data:
            team_data = client.transform_team_data(tsdb_team, League.NFL)
            
            # Check if team already exists
            existing_team = db.query(Team).filter(Team.team_uid == team_data["team_uid"]).first()
            if existing_team:
                # Update existing team
                for field, value in team_data.items():
                    if field not in ['team_uid', 'created_at']:
                        setattr(existing_team, field, value)
                updated_count += 1
                logger.info(f"Updated team: {existing_team.name}")
            else:
                # Create new team
                team = Team(**team_data)
                db.add(team)
                added_count += 1
                logger.info(f"Added team: {team.name}")
        
        db.commit()
        logger.info(f"Teams ingestion completed! Added: {added_count}, Updated: {updated_count}")
        
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
    ingest_all_nfl_teams()