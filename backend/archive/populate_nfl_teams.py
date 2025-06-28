#!/usr/bin/env python3
"""
Populate NFL teams table with comprehensive data including GPS coordinates
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.models.sports import Team

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("nfl_teams_population.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Comprehensive NFL team data with GPS coordinates and metadata
NFL_TEAMS_DATA = [
    {
        "team_uid": "NFL_134946",
        "city": "Arizona",
        "name": "Cardinals",
        "abbreviation": "ARI",
        "stadium_name": "State Farm Stadium",
        "stadium_capacity": 63400,
        "latitude": 33.5276,
        "longitude": -112.2626,
        "founded_year": 1898,
        "conference": "NFC",
        "division": "West"
    },
    {
        "team_uid": "NFL_134942",
        "city": "Atlanta",
        "name": "Falcons",
        "abbreviation": "ATL",
        "stadium_name": "Mercedes-Benz Stadium",
        "stadium_capacity": 71000,
        "latitude": 33.7553,
        "longitude": -84.4006,
        "founded_year": 1966,
        "conference": "NFC",
        "division": "South"
    },
    {
        "team_uid": "NFL_134922",
        "city": "Baltimore",
        "name": "Ravens",
        "abbreviation": "BAL",
        "stadium_name": "M&T Bank Stadium",
        "stadium_capacity": 71008,
        "latitude": 39.2781,
        "longitude": -76.6227,
        "founded_year": 1996,
        "conference": "AFC",
        "division": "North"
    },
    {
        "team_uid": "NFL_134918",
        "city": "Buffalo",
        "name": "Bills",
        "abbreviation": "BUF",
        "stadium_name": "Highmark Stadium",
        "stadium_capacity": 71608,
        "latitude": 42.7738,
        "longitude": -78.7870,
        "founded_year": 1960,
        "conference": "AFC",
        "division": "East"
    },
    {
        "team_uid": "NFL_134943",
        "city": "Carolina",
        "name": "Panthers",
        "abbreviation": "CAR",
        "stadium_name": "Bank of America Stadium",
        "stadium_capacity": 75523,
        "latitude": 35.2258,
        "longitude": -80.8526,
        "founded_year": 1995,
        "conference": "NFC",
        "division": "South"
    },
    {
        "team_uid": "NFL_134938",
        "city": "Chicago",
        "name": "Bears",
        "abbreviation": "CHI",
        "stadium_name": "Soldier Field",
        "stadium_capacity": 61500,
        "latitude": 41.8623,
        "longitude": -87.6167,
        "founded_year": 1920,
        "conference": "NFC",
        "division": "North"
    },
    {
        "team_uid": "NFL_134923",
        "city": "Cincinnati",
        "name": "Bengals",
        "abbreviation": "CIN",
        "stadium_name": "Paycor Stadium",
        "stadium_capacity": 65515,
        "latitude": 39.0955,
        "longitude": -84.5160,
        "founded_year": 1968,
        "conference": "AFC",
        "division": "North"
    },
    {
        "team_uid": "NFL_134924",
        "city": "Cleveland",
        "name": "Browns",
        "abbreviation": "CLE",
        "stadium_name": "Cleveland Browns Stadium",
        "stadium_capacity": 67431,
        "latitude": 41.5061,
        "longitude": -81.6995,
        "founded_year": 1946,
        "conference": "AFC",
        "division": "North"
    },
    {
        "team_uid": "NFL_134934",
        "city": "Dallas",
        "name": "Cowboys",
        "abbreviation": "DAL",
        "stadium_name": "AT&T Stadium",
        "stadium_capacity": 80000,
        "latitude": 32.7473,
        "longitude": -97.0945,
        "founded_year": 1960,
        "conference": "NFC",
        "division": "East"
    },
    {
        "team_uid": "NFL_134930",
        "city": "Denver",
        "name": "Broncos",
        "abbreviation": "DEN",
        "stadium_name": "Empower Field at Mile High",
        "stadium_capacity": 76125,
        "latitude": 39.7439,
        "longitude": -105.0201,
        "founded_year": 1960,
        "conference": "AFC",
        "division": "West"
    },
    {
        "team_uid": "NFL_134939",
        "city": "Detroit",
        "name": "Lions",
        "abbreviation": "DET",
        "stadium_name": "Ford Field",
        "stadium_capacity": 65000,
        "latitude": 42.3400,
        "longitude": -83.0456,
        "founded_year": 1930,
        "conference": "NFC",
        "division": "North"
    },
    {
        "team_uid": "NFL_134940",
        "city": "Green Bay",
        "name": "Packers",
        "abbreviation": "GB",
        "stadium_name": "Lambeau Field",
        "stadium_capacity": 81441,
        "latitude": 44.5013,
        "longitude": -88.0622,
        "founded_year": 1919,
        "conference": "NFC",
        "division": "North"
    },
    {
        "team_uid": "NFL_134926",
        "city": "Houston",
        "name": "Texans",
        "abbreviation": "HOU",
        "stadium_name": "NRG Stadium",
        "stadium_capacity": 72220,
        "latitude": 29.6847,
        "longitude": -95.4107,
        "founded_year": 2002,
        "conference": "AFC",
        "division": "South"
    },
    {
        "team_uid": "NFL_134927",
        "city": "Indianapolis",
        "name": "Colts",
        "abbreviation": "IND",
        "stadium_name": "Lucas Oil Stadium",
        "stadium_capacity": 67000,
        "latitude": 39.7601,
        "longitude": -86.1639,
        "founded_year": 1953,
        "conference": "AFC",
        "division": "South"
    },
    {
        "team_uid": "NFL_134928",
        "city": "Jacksonville",
        "name": "Jaguars",
        "abbreviation": "JAX",
        "stadium_name": "TIAA Bank Field",
        "stadium_capacity": 69132,
        "latitude": 30.3240,
        "longitude": -81.6373,
        "founded_year": 1995,
        "conference": "AFC",
        "division": "South"
    },
    {
        "team_uid": "NFL_134931",
        "city": "Kansas City",
        "name": "Chiefs",
        "abbreviation": "KC",
        "stadium_name": "Arrowhead Stadium",
        "stadium_capacity": 76416,
        "latitude": 39.0489,
        "longitude": -94.4839,
        "founded_year": 1960,
        "conference": "AFC",
        "division": "West"
    },
    {
        "team_uid": "NFL_134932",
        "city": "Las Vegas",
        "name": "Raiders",
        "abbreviation": "LV",
        "stadium_name": "Allegiant Stadium",
        "stadium_capacity": 65000,
        "latitude": 36.0909,
        "longitude": -115.1830,
        "founded_year": 1960,
        "conference": "AFC",
        "division": "West"
    },
    {
        "team_uid": "NFL_135908",
        "city": "Los Angeles",
        "name": "Chargers",
        "abbreviation": "LAC",
        "stadium_name": "SoFi Stadium",
        "stadium_capacity": 70240,
        "latitude": 33.9535,
        "longitude": -118.3392,
        "founded_year": 1960,
        "conference": "AFC",
        "division": "West"
    },
    {
        "team_uid": "NFL_135907",
        "city": "Los Angeles",
        "name": "Rams",
        "abbreviation": "LAR",
        "stadium_name": "SoFi Stadium",
        "stadium_capacity": 70240,
        "latitude": 33.9535,
        "longitude": -118.3392,
        "founded_year": 1936,
        "conference": "NFC",
        "division": "West"
    },
    {
        "team_uid": "NFL_134919",
        "city": "Miami",
        "name": "Dolphins",
        "abbreviation": "MIA",
        "stadium_name": "Hard Rock Stadium",
        "stadium_capacity": 65326,
        "latitude": 25.9580,
        "longitude": -80.2389,
        "founded_year": 1966,
        "conference": "AFC",
        "division": "East"
    },
    {
        "team_uid": "NFL_134941",
        "city": "Minnesota",
        "name": "Vikings",
        "abbreviation": "MIN",
        "stadium_name": "U.S. Bank Stadium",
        "stadium_capacity": 66860,
        "latitude": 44.9738,
        "longitude": -93.2581,
        "founded_year": 1961,
        "conference": "NFC",
        "division": "North"
    },
    {
        "team_uid": "NFL_134920",
        "city": "New England",
        "name": "Patriots",
        "abbreviation": "NE",
        "stadium_name": "Gillette Stadium",
        "stadium_capacity": 66829,
        "latitude": 42.0909,
        "longitude": -71.2643,
        "founded_year": 1960,
        "conference": "AFC",
        "division": "East"
    },
    {
        "team_uid": "NFL_134944",
        "city": "New Orleans",
        "name": "Saints",
        "abbreviation": "NO",
        "stadium_name": "Caesars Superdome",
        "stadium_capacity": 73208,
        "latitude": 29.9511,
        "longitude": -90.0812,
        "founded_year": 1967,
        "conference": "NFC",
        "division": "South"
    },
    {
        "team_uid": "NFL_134935",
        "city": "New York",
        "name": "Giants",
        "abbreviation": "NYG",
        "stadium_name": "MetLife Stadium",
        "stadium_capacity": 82500,
        "latitude": 40.8128,
        "longitude": -74.0742,
        "founded_year": 1925,
        "conference": "NFC",
        "division": "East"
    },
    {
        "team_uid": "NFL_134921",
        "city": "New York",
        "name": "Jets",
        "abbreviation": "NYJ",
        "stadium_name": "MetLife Stadium",
        "stadium_capacity": 82500,
        "latitude": 40.8128,
        "longitude": -74.0742,
        "founded_year": 1960,
        "conference": "AFC",
        "division": "East"
    },
    {
        "team_uid": "NFL_134936",
        "city": "Philadelphia",
        "name": "Eagles",
        "abbreviation": "PHI",
        "stadium_name": "Lincoln Financial Field",
        "stadium_capacity": 69596,
        "latitude": 39.9008,
        "longitude": -75.1675,
        "founded_year": 1933,
        "conference": "NFC",
        "division": "East"
    },
    {
        "team_uid": "NFL_134925",
        "city": "Pittsburgh",
        "name": "Steelers",
        "abbreviation": "PIT",
        "stadium_name": "Acrisure Stadium",
        "stadium_capacity": 68400,
        "latitude": 40.4468,
        "longitude": -80.0158,
        "founded_year": 1933,
        "conference": "AFC",
        "division": "North"
    },
    {
        "team_uid": "NFL_134948",
        "city": "San Francisco",
        "name": "49ers",
        "abbreviation": "SF",
        "stadium_name": "Levi's Stadium",
        "stadium_capacity": 68500,
        "latitude": 37.4032,
        "longitude": -121.9698,
        "founded_year": 1946,
        "conference": "NFC",
        "division": "West"
    },
    {
        "team_uid": "NFL_134949",
        "city": "Seattle",
        "name": "Seahawks",
        "abbreviation": "SEA",
        "stadium_name": "Lumen Field",
        "stadium_capacity": 69000,
        "latitude": 47.5952,
        "longitude": -122.3316,
        "founded_year": 1976,
        "conference": "NFC",
        "division": "West"
    },
    {
        "team_uid": "NFL_134945",
        "city": "Tampa Bay",
        "name": "Buccaneers",
        "abbreviation": "TB",
        "stadium_name": "Raymond James Stadium",
        "stadium_capacity": 65890,
        "latitude": 27.9759,
        "longitude": -82.5033,
        "founded_year": 1976,
        "conference": "NFC",
        "division": "South"
    },
    {
        "team_uid": "NFL_134929",
        "city": "Tennessee",
        "name": "Titans",
        "abbreviation": "TEN",
        "stadium_name": "Nissan Stadium",
        "stadium_capacity": 69143,
        "latitude": 36.1665,
        "longitude": -86.7713,
        "founded_year": 1960,
        "conference": "AFC",
        "division": "South"
    },
    {
        "team_uid": "NFL_134937",
        "city": "Washington",
        "name": "Commanders",
        "abbreviation": "WAS",
        "stadium_name": "FedExField",
        "stadium_capacity": 82000,
        "latitude": 38.9077,
        "longitude": -76.8644,
        "founded_year": 1932,
        "conference": "NFC",
        "division": "East"
    }
]


class NFLTeamsPopulator:
    """Service to populate NFL teams with comprehensive data"""
    
    def __init__(self):
        self.db = None
        
    def __enter__(self):
        self.db = SessionLocal()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.db:
            self.db.close()
    
    def populate_teams(self) -> Dict:
        """Populate or update all NFL teams with comprehensive data"""
        logger.info("Starting NFL teams population")
        
        teams_created = 0
        teams_updated = 0
        
        for team_data in NFL_TEAMS_DATA:
            try:
                # Check if team already exists
                existing_team = self.db.query(Team).filter(
                    Team.team_uid == team_data["team_uid"]
                ).first()
                
                if existing_team:
                    # Update existing team
                    existing_team.league = "NFL"
                    existing_team.city = team_data["city"]
                    existing_team.name = team_data["name"]
                    existing_team.abbreviation = team_data["abbreviation"]
                    existing_team.stadium_name = team_data["stadium_name"]
                    existing_team.stadium_capacity = team_data["stadium_capacity"]
                    existing_team.latitude = team_data["latitude"]
                    existing_team.longitude = team_data["longitude"]
                    existing_team.founded_year = team_data["founded_year"]
                    existing_team.conference = team_data["conference"]
                    existing_team.division = team_data["division"]
                    existing_team.source = "manual_population"
                    existing_team.updated_at = datetime.utcnow()
                    teams_updated += 1
                    
                    logger.info(f"Updated {team_data['city']} {team_data['name']}")
                    
                else:
                    # Create new team
                    new_team = Team(
                        team_uid=team_data["team_uid"],
                        league="NFL",
                        city=team_data["city"],
                        name=team_data["name"],
                        abbreviation=team_data["abbreviation"],
                        stadium_name=team_data["stadium_name"],
                        stadium_capacity=team_data["stadium_capacity"],
                        latitude=team_data["latitude"],
                        longitude=team_data["longitude"],
                        founded_year=team_data["founded_year"],
                        conference=team_data["conference"],
                        division=team_data["division"],
                        source="manual_population"
                    )
                    
                    self.db.add(new_team)
                    teams_created += 1
                    
                    logger.info(f"Created {team_data['city']} {team_data['name']}")
                
            except Exception as e:
                logger.error(f"Failed to process {team_data['city']} {team_data['name']}: {e}")
                self.db.rollback()
                continue
        
        # Commit all changes
        try:
            self.db.commit()
            logger.info("All team data committed successfully")
        except Exception as e:
            logger.error(f"Failed to commit team data: {e}")
            self.db.rollback()
            return {"error": str(e)}
        
        return {
            "teams_created": teams_created,
            "teams_updated": teams_updated,
            "total_teams": len(NFL_TEAMS_DATA),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def verify_teams(self) -> Dict:
        """Verify all teams have complete data"""
        logger.info("Verifying team data completeness")
        
        teams = self.db.query(Team).filter(Team.league == "NFL").all()
        
        complete_teams = 0
        incomplete_teams = []
        
        required_fields = [
            'team_uid', 'city', 'name', 'abbreviation', 'stadium_name',
            'stadium_capacity', 'latitude', 'longitude', 'founded_year',
            'conference', 'division'
        ]
        
        for team in teams:
            missing_fields = []
            for field in required_fields:
                if getattr(team, field) is None:
                    missing_fields.append(field)
            
            if missing_fields:
                incomplete_teams.append({
                    "team": f"{team.city} {team.name}",
                    "missing_fields": missing_fields
                })
            else:
                complete_teams += 1
        
        return {
            "total_teams": len(teams),
            "complete_teams": complete_teams,
            "incomplete_teams": incomplete_teams,
            "completeness_rate": f"{(complete_teams / len(teams)) * 100:.1f}%" if teams else "0%"
        }


async def main():
    """Main execution"""
    logger.info("=" * 80)
    logger.info("NFL TEAMS POPULATION")
    logger.info("=" * 80)
    logger.info("Populating teams table with GPS coordinates and metadata")
    
    try:
        with NFLTeamsPopulator() as service:
            # Populate teams
            results = service.populate_teams()
            
            if "error" in results:
                logger.error(f"❌ POPULATION FAILED: {results['error']}")
                return 1
            
            # Verify completeness
            verification = service.verify_teams()
            
            logger.info("\n" + "=" * 60)
            logger.info("POPULATION COMPLETE - SUMMARY")
            logger.info("=" * 60)
            logger.info(f"Teams created: {results['teams_created']}")
            logger.info(f"Teams updated: {results['teams_updated']}")
            logger.info(f"Total teams: {results['total_teams']}")
            logger.info(f"Data completeness: {verification['completeness_rate']}")
            
            if verification['incomplete_teams']:
                logger.warning(f"⚠️  {len(verification['incomplete_teams'])} teams have missing data:")
                for team in verification['incomplete_teams']:
                    logger.warning(f"  {team['team']}: missing {', '.join(team['missing_fields'])}")
            
            logger.info("\n✅ NFL TEAMS POPULATION COMPLETE!")
            logger.info("📍 All teams now have GPS coordinates and metadata")
            
            return 0
            
    except Exception as e:
        logger.error(f"❌ POPULATION FAILED: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)