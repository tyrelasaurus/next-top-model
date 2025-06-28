#!/usr/bin/env python3
"""
Populate teams table with NFL teams for proper foreign key relationships
"""

import sys
from pathlib import Path
import logging

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.models.sports import Team

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def populate_nfl_teams():
    """Populate the teams table with all NFL teams"""
    logger.info("Populating NFL teams...")
    
    db = SessionLocal()
    try:
        nfl_teams = [
            {'team_uid': 'NFL_134946', 'name': 'Arizona Cardinals', 'city': 'Arizona', 'abbreviation': 'ARI', 'conference': 'NFC', 'division': 'West'},
            {'team_uid': 'NFL_134942', 'name': 'Atlanta Falcons', 'city': 'Atlanta', 'abbreviation': 'ATL', 'conference': 'NFC', 'division': 'South'},
            {'team_uid': 'NFL_134922', 'name': 'Baltimore Ravens', 'city': 'Baltimore', 'abbreviation': 'BAL', 'conference': 'AFC', 'division': 'North'},
            {'team_uid': 'NFL_134918', 'name': 'Buffalo Bills', 'city': 'Buffalo', 'abbreviation': 'BUF', 'conference': 'AFC', 'division': 'East'},
            {'team_uid': 'NFL_134943', 'name': 'Carolina Panthers', 'city': 'Carolina', 'abbreviation': 'CAR', 'conference': 'NFC', 'division': 'South'},
            {'team_uid': 'NFL_134938', 'name': 'Chicago Bears', 'city': 'Chicago', 'abbreviation': 'CHI', 'conference': 'NFC', 'division': 'North'},
            {'team_uid': 'NFL_134923', 'name': 'Cincinnati Bengals', 'city': 'Cincinnati', 'abbreviation': 'CIN', 'conference': 'AFC', 'division': 'North'},
            {'team_uid': 'NFL_134924', 'name': 'Cleveland Browns', 'city': 'Cleveland', 'abbreviation': 'CLE', 'conference': 'AFC', 'division': 'North'},
            {'team_uid': 'NFL_134934', 'name': 'Dallas Cowboys', 'city': 'Dallas', 'abbreviation': 'DAL', 'conference': 'NFC', 'division': 'East'},
            {'team_uid': 'NFL_134930', 'name': 'Denver Broncos', 'city': 'Denver', 'abbreviation': 'DEN', 'conference': 'AFC', 'division': 'West'},
            {'team_uid': 'NFL_134939', 'name': 'Detroit Lions', 'city': 'Detroit', 'abbreviation': 'DET', 'conference': 'NFC', 'division': 'North'},
            {'team_uid': 'NFL_134940', 'name': 'Green Bay Packers', 'city': 'Green Bay', 'abbreviation': 'GB', 'conference': 'NFC', 'division': 'North'},
            {'team_uid': 'NFL_134926', 'name': 'Houston Texans', 'city': 'Houston', 'abbreviation': 'HOU', 'conference': 'AFC', 'division': 'South'},
            {'team_uid': 'NFL_134927', 'name': 'Indianapolis Colts', 'city': 'Indianapolis', 'abbreviation': 'IND', 'conference': 'AFC', 'division': 'South'},
            {'team_uid': 'NFL_134928', 'name': 'Jacksonville Jaguars', 'city': 'Jacksonville', 'abbreviation': 'JAX', 'conference': 'AFC', 'division': 'South'},
            {'team_uid': 'NFL_134931', 'name': 'Kansas City Chiefs', 'city': 'Kansas City', 'abbreviation': 'KC', 'conference': 'AFC', 'division': 'West'},
            {'team_uid': 'NFL_134932', 'name': 'Las Vegas Raiders', 'city': 'Las Vegas', 'abbreviation': 'LV', 'conference': 'AFC', 'division': 'West'},
            {'team_uid': 'NFL_135908', 'name': 'Los Angeles Chargers', 'city': 'Los Angeles', 'abbreviation': 'LAC', 'conference': 'AFC', 'division': 'West'},
            {'team_uid': 'NFL_135907', 'name': 'Los Angeles Rams', 'city': 'Los Angeles', 'abbreviation': 'LAR', 'conference': 'NFC', 'division': 'West'},
            {'team_uid': 'NFL_134919', 'name': 'Miami Dolphins', 'city': 'Miami', 'abbreviation': 'MIA', 'conference': 'AFC', 'division': 'East'},
            {'team_uid': 'NFL_134941', 'name': 'Minnesota Vikings', 'city': 'Minnesota', 'abbreviation': 'MIN', 'conference': 'NFC', 'division': 'North'},
            {'team_uid': 'NFL_134920', 'name': 'New England Patriots', 'city': 'New England', 'abbreviation': 'NE', 'conference': 'AFC', 'division': 'East'},
            {'team_uid': 'NFL_134944', 'name': 'New Orleans Saints', 'city': 'New Orleans', 'abbreviation': 'NO', 'conference': 'NFC', 'division': 'South'},
            {'team_uid': 'NFL_134935', 'name': 'New York Giants', 'city': 'New York', 'abbreviation': 'NYG', 'conference': 'NFC', 'division': 'East'},
            {'team_uid': 'NFL_134921', 'name': 'New York Jets', 'city': 'New York', 'abbreviation': 'NYJ', 'conference': 'AFC', 'division': 'East'},
            {'team_uid': 'NFL_134936', 'name': 'Philadelphia Eagles', 'city': 'Philadelphia', 'abbreviation': 'PHI', 'conference': 'NFC', 'division': 'East'},
            {'team_uid': 'NFL_134925', 'name': 'Pittsburgh Steelers', 'city': 'Pittsburgh', 'abbreviation': 'PIT', 'conference': 'AFC', 'division': 'North'},
            {'team_uid': 'NFL_134948', 'name': 'San Francisco 49ers', 'city': 'San Francisco', 'abbreviation': 'SF', 'conference': 'NFC', 'division': 'West'},
            {'team_uid': 'NFL_134949', 'name': 'Seattle Seahawks', 'city': 'Seattle', 'abbreviation': 'SEA', 'conference': 'NFC', 'division': 'West'},
            {'team_uid': 'NFL_134945', 'name': 'Tampa Bay Buccaneers', 'city': 'Tampa Bay', 'abbreviation': 'TB', 'conference': 'NFC', 'division': 'South'},
            {'team_uid': 'NFL_134929', 'name': 'Tennessee Titans', 'city': 'Tennessee', 'abbreviation': 'TEN', 'conference': 'AFC', 'division': 'South'},
            {'team_uid': 'NFL_134937', 'name': 'Washington Commanders', 'city': 'Washington', 'abbreviation': 'WAS', 'conference': 'NFC', 'division': 'East'}
        ]
        
        teams_added = 0
        teams_updated = 0
        
        for team_data in nfl_teams:
            existing_team = db.query(Team).filter(Team.team_uid == team_data['team_uid']).first()
            
            if existing_team:
                # Update existing team
                for key, value in team_data.items():
                    if hasattr(existing_team, key):
                        setattr(existing_team, key, value)
                teams_updated += 1
            else:
                # Create new team
                team = Team(
                    team_uid=team_data['team_uid'],
                    name=team_data['name'],
                    city=team_data['city'],
                    abbreviation=team_data['abbreviation'],
                    conference=team_data['conference'],
                    division=team_data['division'],
                    league='NFL',
                    source='manual_population'
                )
                db.add(team)
                teams_added += 1
        
        db.commit()
        
        logger.info(f"Teams populated successfully!")
        logger.info(f"  - Teams added: {teams_added}")
        logger.info(f"  - Teams updated: {teams_updated}")
        logger.info(f"  - Total teams: {teams_added + teams_updated}")
        
        return teams_added + teams_updated
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to populate teams: {e}")
        raise
    finally:
        db.close()


def main():
    """Main execution"""
    logger.info("NFL Teams Population Script")
    logger.info("=" * 40)
    
    try:
        team_count = populate_nfl_teams()
        logger.info(f"✅ Successfully populated {team_count} NFL teams")
        
    except Exception as e:
        logger.error(f"❌ Failed to populate teams: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)