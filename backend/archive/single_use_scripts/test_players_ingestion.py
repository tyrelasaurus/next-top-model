#!/usr/bin/env python3
"""Test script to ingest players for a few NFL teams"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.ingestion.thesportsdb import TheSportsDBClient
from backend.app.models import Team, Player, League
from backend.app.core.database import SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_player_ingestion():
    """Test player ingestion for a few teams"""
    client = TheSportsDBClient()
    db = SessionLocal()
    
    try:
        # Get first 3 teams to test with
        teams = db.query(Team).filter(Team.league == League.NFL).limit(3).all()
        logger.info(f"Testing player ingestion for {len(teams)} teams")
        
        total_added = 0
        
        for team in teams:
            logger.info(f"Testing players for: {team.name}")
            
            # Extract team ID from team_uid (format: NFL_134918)
            team_id = team.team_uid.split('_')[1]
            
            try:
                players_data = client.get_players_by_team(team_id)
                logger.info(f"Found {len(players_data)} players for {team.name}")
                
                if players_data:
                    # Just test transformation, don't save to avoid clutter
                    for i, tsdb_player in enumerate(players_data[:3]):  # Test first 3 players
                        try:
                            player_data = client.transform_player_data(tsdb_player, team.team_uid)
                            logger.info(f"  Player {i+1}: {player_data.get('name', 'Unknown')} - {player_data.get('position', 'N/A')}")
                        except Exception as e:
                            logger.warning(f"Error transforming player {i+1}: {e}")
                
            except Exception as e:
                logger.warning(f"Error fetching players for {team.name}: {e}")
                
        logger.info("Player ingestion test completed!")
        
    except Exception as e:
        logger.error(f"Error during player test: {e}")
        raise
    finally:
        client.close()
        db.close()


if __name__ == "__main__":
    test_player_ingestion()