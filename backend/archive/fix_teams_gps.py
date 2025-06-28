#!/usr/bin/env python3
"""
Direct SQL update to fix teams GPS coordinates
"""

import sqlite3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# GPS coordinates data for NFL teams
TEAMS_GPS_DATA = {
    "NFL_134946": {"stadium_name": "State Farm Stadium", "latitude": 33.5276, "longitude": -112.2626, "stadium_capacity": 63400, "conference": "NFC", "division": "West", "founded_year": 1898},
    "NFL_134942": {"stadium_name": "Mercedes-Benz Stadium", "latitude": 33.7553, "longitude": -84.4006, "stadium_capacity": 71000, "conference": "NFC", "division": "South", "founded_year": 1966},
    "NFL_134922": {"stadium_name": "M&T Bank Stadium", "latitude": 39.2781, "longitude": -76.6227, "stadium_capacity": 71008, "conference": "AFC", "division": "North", "founded_year": 1996},
    "NFL_134918": {"stadium_name": "Highmark Stadium", "latitude": 42.7738, "longitude": -78.7870, "stadium_capacity": 71608, "conference": "AFC", "division": "East", "founded_year": 1960},
    "NFL_134943": {"stadium_name": "Bank of America Stadium", "latitude": 35.2258, "longitude": -80.8526, "stadium_capacity": 75523, "conference": "NFC", "division": "South", "founded_year": 1995},
    "NFL_134938": {"stadium_name": "Soldier Field", "latitude": 41.8623, "longitude": -87.6167, "stadium_capacity": 61500, "conference": "NFC", "division": "North", "founded_year": 1920},
    "NFL_134923": {"stadium_name": "Paycor Stadium", "latitude": 39.0955, "longitude": -84.5160, "stadium_capacity": 65515, "conference": "AFC", "division": "North", "founded_year": 1968},
    "NFL_134924": {"stadium_name": "Cleveland Browns Stadium", "latitude": 41.5061, "longitude": -81.6995, "stadium_capacity": 67431, "conference": "AFC", "division": "North", "founded_year": 1946},
    "NFL_134934": {"stadium_name": "AT&T Stadium", "latitude": 32.7473, "longitude": -97.0945, "stadium_capacity": 80000, "conference": "NFC", "division": "East", "founded_year": 1960},
    "NFL_134930": {"stadium_name": "Empower Field at Mile High", "latitude": 39.7439, "longitude": -105.0201, "stadium_capacity": 76125, "conference": "AFC", "division": "West", "founded_year": 1960},
    "NFL_134939": {"stadium_name": "Ford Field", "latitude": 42.3400, "longitude": -83.0456, "stadium_capacity": 65000, "conference": "NFC", "division": "North", "founded_year": 1930},
    "NFL_134940": {"stadium_name": "Lambeau Field", "latitude": 44.5013, "longitude": -88.0622, "stadium_capacity": 81441, "conference": "NFC", "division": "North", "founded_year": 1919},
    "NFL_134926": {"stadium_name": "NRG Stadium", "latitude": 29.6847, "longitude": -95.4107, "stadium_capacity": 72220, "conference": "AFC", "division": "South", "founded_year": 2002},
    "NFL_134927": {"stadium_name": "Lucas Oil Stadium", "latitude": 39.7601, "longitude": -86.1639, "stadium_capacity": 67000, "conference": "AFC", "division": "South", "founded_year": 1953},
    "NFL_134928": {"stadium_name": "TIAA Bank Field", "latitude": 30.3240, "longitude": -81.6373, "stadium_capacity": 69132, "conference": "AFC", "division": "South", "founded_year": 1995},
    "NFL_134931": {"stadium_name": "Arrowhead Stadium", "latitude": 39.0489, "longitude": -94.4839, "stadium_capacity": 76416, "conference": "AFC", "division": "West", "founded_year": 1960},
    "NFL_134932": {"stadium_name": "Allegiant Stadium", "latitude": 36.0909, "longitude": -115.1830, "stadium_capacity": 65000, "conference": "AFC", "division": "West", "founded_year": 1960},
    "NFL_135908": {"stadium_name": "SoFi Stadium", "latitude": 33.9535, "longitude": -118.3392, "stadium_capacity": 70240, "conference": "AFC", "division": "West", "founded_year": 1960},
    "NFL_135907": {"stadium_name": "SoFi Stadium", "latitude": 33.9535, "longitude": -118.3392, "stadium_capacity": 70240, "conference": "NFC", "division": "West", "founded_year": 1936},
    "NFL_134919": {"stadium_name": "Hard Rock Stadium", "latitude": 25.9580, "longitude": -80.2389, "stadium_capacity": 65326, "conference": "AFC", "division": "East", "founded_year": 1966},
    "NFL_134941": {"stadium_name": "U.S. Bank Stadium", "latitude": 44.9738, "longitude": -93.2581, "stadium_capacity": 66860, "conference": "NFC", "division": "North", "founded_year": 1961},
    "NFL_134920": {"stadium_name": "Gillette Stadium", "latitude": 42.0909, "longitude": -71.2643, "stadium_capacity": 66829, "conference": "AFC", "division": "East", "founded_year": 1960},
    "NFL_134944": {"stadium_name": "Caesars Superdome", "latitude": 29.9511, "longitude": -90.0812, "stadium_capacity": 73208, "conference": "NFC", "division": "South", "founded_year": 1967},
    "NFL_134935": {"stadium_name": "MetLife Stadium", "latitude": 40.8128, "longitude": -74.0742, "stadium_capacity": 82500, "conference": "NFC", "division": "East", "founded_year": 1925},
    "NFL_134921": {"stadium_name": "MetLife Stadium", "latitude": 40.8128, "longitude": -74.0742, "stadium_capacity": 82500, "conference": "AFC", "division": "East", "founded_year": 1960},
    "NFL_134936": {"stadium_name": "Lincoln Financial Field", "latitude": 39.9008, "longitude": -75.1675, "stadium_capacity": 69596, "conference": "NFC", "division": "East", "founded_year": 1933},
    "NFL_134925": {"stadium_name": "Acrisure Stadium", "latitude": 40.4468, "longitude": -80.0158, "stadium_capacity": 68400, "conference": "AFC", "division": "North", "founded_year": 1933},
    "NFL_134948": {"stadium_name": "Levi's Stadium", "latitude": 37.4032, "longitude": -121.9698, "stadium_capacity": 68500, "conference": "NFC", "division": "West", "founded_year": 1946},
    "NFL_134949": {"stadium_name": "Lumen Field", "latitude": 47.5952, "longitude": -122.3316, "stadium_capacity": 69000, "conference": "NFC", "division": "West", "founded_year": 1976},
    "NFL_134945": {"stadium_name": "Raymond James Stadium", "latitude": 27.9759, "longitude": -82.5033, "stadium_capacity": 65890, "conference": "NFC", "division": "South", "founded_year": 1976},
    "NFL_134929": {"stadium_name": "Nissan Stadium", "latitude": 36.1665, "longitude": -86.7713, "stadium_capacity": 69143, "conference": "AFC", "division": "South", "founded_year": 1960},
    "NFL_134937": {"stadium_name": "FedExField", "latitude": 38.9077, "longitude": -76.8644, "stadium_capacity": 82000, "conference": "NFC", "division": "East", "founded_year": 1932}
}

def update_teams_gps():
    """Update teams table with GPS coordinates using direct SQL"""
    logger.info("Updating teams with GPS coordinates using direct SQL")
    
    # Connect to database
    conn = sqlite3.connect('nfl_data.db')
    cursor = conn.cursor()
    
    teams_updated = 0
    
    for team_uid, data in TEAMS_GPS_DATA.items():
        try:
            cursor.execute("""
                UPDATE teams 
                SET stadium_name = ?, 
                    latitude = ?, 
                    longitude = ?, 
                    stadium_capacity = ?,
                    conference = ?,
                    division = ?,
                    founded_year = ?
                WHERE team_uid = ?
            """, (
                data["stadium_name"],
                data["latitude"], 
                data["longitude"],
                data["stadium_capacity"],
                data["conference"],
                data["division"],
                data["founded_year"],
                team_uid
            ))
            
            if cursor.rowcount > 0:
                teams_updated += 1
                logger.info(f"Updated {team_uid}")
            
        except Exception as e:
            logger.error(f"Failed to update {team_uid}: {e}")
    
    # Commit changes
    conn.commit()
    
    # Verify results
    cursor.execute("SELECT COUNT(*) FROM teams WHERE latitude IS NOT NULL")
    teams_with_gps = cursor.fetchone()[0]
    
    conn.close()
    
    logger.info(f"✅ Updated {teams_updated} teams")
    logger.info(f"✅ {teams_with_gps} teams now have GPS coordinates")
    
    return teams_updated

if __name__ == "__main__":
    updated = update_teams_gps()
    print(f"Updated {updated} teams with GPS coordinates")