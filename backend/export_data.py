#!/usr/bin/env python3
"""Export NFL data to structured CSV and JSON files"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.core.database import SessionLocal
from backend.app.models import Team, Game, League
import pandas as pd
import json
import logging
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enhanced team information with stadium details
NFL_TEAM_DETAILS = {
    "NFL_134918": {  # Buffalo Bills
        "city": "Buffalo",
        "state": "NY",
        "division": "AFC East",
        "stadium_name": "Highmark Stadium",
        "stadium_capacity": 71608,
        "stadium_surface": "Artificial Turf",
        "stadium_gps": {"lat": 42.7738, "lng": -78.7867},
        "founded": 1960,
        "colors": ["#00338D", "#C60C30"],
        "head_coach": "Sean McDermott"
    },
    "NFL_134919": {  # Miami Dolphins
        "city": "Miami Gardens",
        "state": "FL", 
        "division": "AFC East",
        "stadium_name": "Hard Rock Stadium",
        "stadium_capacity": 65326,
        "stadium_surface": "Grass",
        "stadium_gps": {"lat": 25.9580, "lng": -80.2389},
        "founded": 1966,
        "colors": ["#008E97", "#FC4C02", "#005778"],
        "head_coach": "Mike McDaniel"
    },
    "NFL_134920": {  # New England Patriots
        "city": "Foxborough",
        "state": "MA",
        "division": "AFC East", 
        "stadium_name": "Gillette Stadium",
        "stadium_capacity": 65878,
        "stadium_surface": "Artificial Turf",
        "stadium_gps": {"lat": 42.0909, "lng": -71.2643},
        "founded": 1960,
        "colors": ["#002244", "#C60C30", "#B0B7BC"],
        "head_coach": "Jerod Mayo"
    },
    "NFL_134921": {  # New York Jets
        "city": "East Rutherford",
        "state": "NJ",
        "division": "AFC East",
        "stadium_name": "MetLife Stadium", 
        "stadium_capacity": 82500,
        "stadium_surface": "Artificial Turf",
        "stadium_gps": {"lat": 40.8135, "lng": -74.0745},
        "founded": 1960,
        "colors": ["#125740", "#000000", "#FFFFFF"],
        "head_coach": "Robert Saleh"
    },
    "NFL_134922": {  # Baltimore Ravens
        "city": "Baltimore",
        "state": "MD",
        "division": "AFC North",
        "stadium_name": "M&T Bank Stadium",
        "stadium_capacity": 71008,
        "stadium_surface": "Grass", 
        "stadium_gps": {"lat": 39.2780, "lng": -76.6227},
        "founded": 1996,
        "colors": ["#241773", "#000000", "#9E7C0C"],
        "head_coach": "John Harbaugh"
    },
    "NFL_134923": {  # Cincinnati Bengals
        "city": "Cincinnati",
        "state": "OH",
        "division": "AFC North",
        "stadium_name": "Paycor Stadium",
        "stadium_capacity": 65515,
        "stadium_surface": "Artificial Turf",
        "stadium_gps": {"lat": 39.0955, "lng": -84.5161},
        "founded": 1968,
        "colors": ["#FB4F14", "#000000"],
        "head_coach": "Zac Taylor"
    },
    "NFL_134924": {  # Cleveland Browns
        "city": "Cleveland", 
        "state": "OH",
        "division": "AFC North",
        "stadium_name": "FirstEnergy Stadium",
        "stadium_capacity": 67431,
        "stadium_surface": "Grass",
        "stadium_gps": {"lat": 41.5061, "lng": -81.6995},
        "founded": 1946,
        "colors": ["#311D00", "#FF3C00"],
        "head_coach": "Kevin Stefanski"
    },
    "NFL_134925": {  # Pittsburgh Steelers
        "city": "Pittsburgh",
        "state": "PA",
        "division": "AFC North",
        "stadium_name": "Acrisure Stadium",
        "stadium_capacity": 68400,
        "stadium_surface": "Grass",
        "stadium_gps": {"lat": 40.4468, "lng": -80.0158},
        "founded": 1933,
        "colors": ["#FFB612", "#101820"],
        "head_coach": "Mike Tomlin"
    },
    "NFL_134926": {  # Houston Texans
        "city": "Houston",
        "state": "TX",
        "division": "AFC South",
        "stadium_name": "NRG Stadium",
        "stadium_capacity": 72220,
        "stadium_surface": "Grass",
        "stadium_gps": {"lat": 29.6847, "lng": -95.4107},
        "founded": 2002,
        "colors": ["#03202F", "#A71930"],
        "head_coach": "DeMeco Ryans"
    },
    "NFL_134927": {  # Indianapolis Colts
        "city": "Indianapolis",
        "state": "IN", 
        "division": "AFC South",
        "stadium_name": "Lucas Oil Stadium",
        "stadium_capacity": 67000,
        "stadium_surface": "Artificial Turf",
        "stadium_gps": {"lat": 39.7601, "lng": -86.1639},
        "founded": 1953,
        "colors": ["#002C5F", "#A2AAAD"],
        "head_coach": "Shane Steichen"
    },
    "NFL_134928": {  # Jacksonville Jaguars
        "city": "Jacksonville",
        "state": "FL",
        "division": "AFC South",
        "stadium_name": "TIAA Bank Field",
        "stadium_capacity": 69132,
        "stadium_surface": "Grass",
        "stadium_gps": {"lat": 30.3240, "lng": -81.6374},
        "founded": 1995,
        "colors": ["#006778", "#9F792C", "#000000"],
        "head_coach": "Doug Pederson"
    },
    "NFL_134929": {  # Tennessee Titans
        "city": "Nashville",
        "state": "TN",
        "division": "AFC South", 
        "stadium_name": "Nissan Stadium",
        "stadium_capacity": 69143,
        "stadium_surface": "Grass",
        "stadium_gps": {"lat": 36.1665, "lng": -86.7713},
        "founded": 1960,
        "colors": ["#0C2340", "#4B92DB", "#C8102E"],
        "head_coach": "Brian Callahan"
    },
    "NFL_134930": {  # Denver Broncos
        "city": "Denver",
        "state": "CO",
        "division": "AFC West",
        "stadium_name": "Empower Field at Mile High",
        "stadium_capacity": 76125,
        "stadium_surface": "Grass",
        "stadium_gps": {"lat": 39.7439, "lng": -105.0201},
        "founded": 1960,
        "colors": ["#FB4F14", "#002244"],
        "head_coach": "Sean Payton"
    },
    "NFL_134931": {  # Kansas City Chiefs
        "city": "Kansas City",
        "state": "MO",
        "division": "AFC West",
        "stadium_name": "GEHA Field at Arrowhead Stadium", 
        "stadium_capacity": 76416,
        "stadium_surface": "Grass",
        "stadium_gps": {"lat": 39.0489, "lng": -94.4839},
        "founded": 1960,
        "colors": ["#E31837", "#FFB81C"],
        "head_coach": "Andy Reid"
    },
    "NFL_134932": {  # Las Vegas Raiders
        "city": "Las Vegas",
        "state": "NV",
        "division": "AFC West",
        "stadium_name": "Allegiant Stadium",
        "stadium_capacity": 65000,
        "stadium_surface": "Grass",
        "stadium_gps": {"lat": 36.0909, "lng": -115.1833},
        "founded": 1960,
        "colors": ["#000000", "#A5ACAF"],
        "head_coach": "Antonio Pierce"
    },
    "NFL_135908": {  # Los Angeles Chargers
        "city": "Los Angeles",
        "state": "CA",
        "division": "AFC West",
        "stadium_name": "SoFi Stadium",
        "stadium_capacity": 70240,
        "stadium_surface": "Artificial Turf",
        "stadium_gps": {"lat": 33.9535, "lng": -118.3392},
        "founded": 1960,
        "colors": ["#0080C6", "#FFC20E", "#FFFFFF"],
        "head_coach": "Jim Harbaugh"
    },
    "NFL_134934": {  # Dallas Cowboys
        "city": "Arlington",
        "state": "TX",
        "division": "NFC East",
        "stadium_name": "AT&T Stadium",
        "stadium_capacity": 80000,
        "stadium_surface": "Artificial Turf",
        "stadium_gps": {"lat": 32.7473, "lng": -97.0945},
        "founded": 1960,
        "colors": ["#003594", "#041E42", "#869397"],
        "head_coach": "Mike McCarthy"
    },
    "NFL_134935": {  # New York Giants
        "city": "East Rutherford",
        "state": "NJ",
        "division": "NFC East",
        "stadium_name": "MetLife Stadium",
        "stadium_capacity": 82500,
        "stadium_surface": "Artificial Turf", 
        "stadium_gps": {"lat": 40.8135, "lng": -74.0745},
        "founded": 1925,
        "colors": ["#0B2265", "#A71930", "#A5ACAF"],
        "head_coach": "Brian Daboll"
    },
    "NFL_134936": {  # Philadelphia Eagles
        "city": "Philadelphia",
        "state": "PA",
        "division": "NFC East",
        "stadium_name": "Lincoln Financial Field",
        "stadium_capacity": 69176,
        "stadium_surface": "Grass",
        "stadium_gps": {"lat": 39.9008, "lng": -75.1675},
        "founded": 1933,
        "colors": ["#004C54", "#A5ACAF", "#ACC0C6"],
        "head_coach": "Nick Sirianni"
    },
    "NFL_134937": {  # Washington Commanders
        "city": "Landover",
        "state": "MD",
        "division": "NFC East",
        "stadium_name": "FedExField",
        "stadium_capacity": 82000,
        "stadium_surface": "Grass",
        "stadium_gps": {"lat": 38.9076, "lng": -76.8645},
        "founded": 1932,
        "colors": ["#5A1414", "#FFB612"],
        "head_coach": "Dan Quinn"
    },
    "NFL_134938": {  # Chicago Bears
        "city": "Chicago",
        "state": "IL",
        "division": "NFC North",
        "stadium_name": "Soldier Field",
        "stadium_capacity": 61500,
        "stadium_surface": "Grass",
        "stadium_gps": {"lat": 41.8623, "lng": -87.6167},
        "founded": 1920,
        "colors": ["#0B162A", "#C83803"],
        "head_coach": "Matt Eberflus"
    },
    "NFL_134939": {  # Detroit Lions
        "city": "Detroit",
        "state": "MI",
        "division": "NFC North",
        "stadium_name": "Ford Field",
        "stadium_capacity": 65000,
        "stadium_surface": "Artificial Turf",
        "stadium_gps": {"lat": 42.3400, "lng": -83.0456},
        "founded": 1930,
        "colors": ["#0076B6", "#B0B7BC", "#000000"],
        "head_coach": "Dan Campbell"
    },
    "NFL_134940": {  # Green Bay Packers
        "city": "Green Bay",
        "state": "WI",
        "division": "NFC North",
        "stadium_name": "Lambeau Field",
        "stadium_capacity": 81441,
        "stadium_surface": "Grass",
        "stadium_gps": {"lat": 44.5013, "lng": -88.0622},
        "founded": 1919,
        "colors": ["#203731", "#FFB612"],
        "head_coach": "Matt LaFleur"
    },
    "NFL_134941": {  # Minnesota Vikings
        "city": "Minneapolis", 
        "state": "MN",
        "division": "NFC North",
        "stadium_name": "U.S. Bank Stadium",
        "stadium_capacity": 66860,
        "stadium_surface": "Artificial Turf",
        "stadium_gps": {"lat": 44.9738, "lng": -93.2581},
        "founded": 1961,
        "colors": ["#4F2683", "#FFC62F"],
        "head_coach": "Kevin O'Connell"
    },
    "NFL_134942": {  # Atlanta Falcons
        "city": "Atlanta",
        "state": "GA",
        "division": "NFC South",
        "stadium_name": "Mercedes-Benz Stadium",
        "stadium_capacity": 71000,
        "stadium_surface": "Artificial Turf",
        "stadium_gps": {"lat": 33.7553, "lng": -84.4006},
        "founded": 1966,
        "colors": ["#A71930", "#000000", "#A5ACAF"],
        "head_coach": "Raheem Morris"
    },
    "NFL_134943": {  # Carolina Panthers
        "city": "Charlotte",
        "state": "NC",
        "division": "NFC South",
        "stadium_name": "Bank of America Stadium",
        "stadium_capacity": 75523,
        "stadium_surface": "Grass",
        "stadium_gps": {"lat": 35.2258, "lng": -80.8531},
        "founded": 1995,
        "colors": ["#0085CA", "#101820", "#BFC0BF"],
        "head_coach": "Dave Canales"
    },
    "NFL_134944": {  # New Orleans Saints
        "city": "New Orleans",
        "state": "LA",
        "division": "NFC South",
        "stadium_name": "Caesars Superdome",
        "stadium_capacity": 73208,
        "stadium_surface": "Artificial Turf",
        "stadium_gps": {"lat": 29.9511, "lng": -90.0812},
        "founded": 1967,
        "colors": ["#D3BC8D", "#101820"],
        "head_coach": "Dennis Allen"
    },
    "NFL_134945": {  # Tampa Bay Buccaneers
        "city": "Tampa",
        "state": "FL",
        "division": "NFC South",
        "stadium_name": "Raymond James Stadium",
        "stadium_capacity": 69218,
        "stadium_surface": "Grass",
        "stadium_gps": {"lat": 27.9759, "lng": -82.5033},
        "founded": 1976,
        "colors": ["#D50A0A", "#FF7900", "#0A0A08"],
        "head_coach": "Todd Bowles"
    },
    "NFL_134946": {  # Arizona Cardinals
        "city": "Glendale",
        "state": "AZ",
        "division": "NFC West",
        "stadium_name": "State Farm Stadium",
        "stadium_capacity": 63400,
        "stadium_surface": "Grass",
        "stadium_gps": {"lat": 33.5276, "lng": -112.2626},
        "founded": 1898,
        "colors": ["#97233F", "#000000", "#FFB612"],
        "head_coach": "Jonathan Gannon"
    },
    "NFL_135907": {  # Los Angeles Rams
        "city": "Los Angeles",
        "state": "CA",
        "division": "NFC West",
        "stadium_name": "SoFi Stadium",
        "stadium_capacity": 70240,
        "stadium_surface": "Artificial Turf",
        "stadium_gps": {"lat": 33.9535, "lng": -118.3392},
        "founded": 1936,
        "colors": ["#003594", "#FFA300", "#FF8200"],
        "head_coach": "Sean McVay"
    },
    "NFL_134948": {  # San Francisco 49ers
        "city": "Santa Clara",
        "state": "CA",
        "division": "NFC West",
        "stadium_name": "Levi's Stadium",
        "stadium_capacity": 68500,
        "stadium_surface": "Grass",
        "stadium_gps": {"lat": 37.4030, "lng": -121.9697},
        "founded": 1946,
        "colors": ["#AA0000", "#B3995D"],
        "head_coach": "Kyle Shanahan"
    },
    "NFL_134949": {  # Seattle Seahawks
        "city": "Seattle",
        "state": "WA",
        "division": "NFC West",
        "stadium_name": "Lumen Field",
        "stadium_capacity": 69000,
        "stadium_surface": "Artificial Turf",
        "stadium_gps": {"lat": 47.5952, "lng": -122.3316},
        "founded": 1976,
        "colors": ["#002244", "#69BE28", "#A5ACAF"],
        "head_coach": "Mike Macdonald"
    }
}


class NFLDataExporter:
    def __init__(self):
        self.db = SessionLocal()
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
        
    def _format_game_datetime(self, game_datetime):
        """Format game datetime - show just date if we don't have real kickoff time"""
        if not game_datetime:
            return None
            
        # If time is 12:00 (our indicator for date-only), show just the date
        if game_datetime.hour == 12 and game_datetime.minute == 0 and game_datetime.second == 0:
            return game_datetime.date().isoformat()
        else:
            # We have a real kickoff time, show full datetime
            return game_datetime.isoformat()

    def export_games_to_csv(self):
        """Export all games data to CSV files"""
        logger.info("Exporting games data to CSV files...")
        
        # Get all NFL games
        games = self.db.query(Game).filter(Game.league == League.NFL).all()
        
        games_data = []
        for game in games:
            games_data.append({
                "game_id": game.game_uid,
                "season": game.season,
                "week": game.week,
                "game_type": game.game_type,
                "date": self._format_game_datetime(game.game_datetime),
                "home_team": game.home_team.name if game.home_team else None,
                "away_team": game.away_team.name if game.away_team else None,
                "home_team_uid": game.home_team_uid,
                "away_team_uid": game.away_team_uid,
                "home_score": game.home_score,
                "away_score": game.away_score,
                "total_points": (game.home_score or 0) + (game.away_score or 0),
                "point_differential": abs((game.home_score or 0) - (game.away_score or 0)),
                "winner": "home" if (game.home_score or 0) > (game.away_score or 0) else "away" if (game.away_score or 0) > (game.home_score or 0) else "tie",
                "source": game.source
            })
        
        # Export complete games dataset
        df_all = pd.DataFrame(games_data)
        df_all.to_csv(self.data_dir / "nfl_games_complete.csv", index=False)
        logger.info(f"Exported {len(games_data)} games to nfl_games_complete.csv")
        
        # Export by season
        for season in [2022, 2023, 2024]:
            df_season = df_all[df_all['season'] == season]
            df_season.to_csv(self.data_dir / f"nfl_games_{season}.csv", index=False)
            logger.info(f"Exported {len(df_season)} games for {season} season")
            
        # Export schedule (future games) vs results (completed games)
        df_completed = df_all[df_all['home_score'].notna() & df_all['away_score'].notna()]
        df_scheduled = df_all[df_all['home_score'].isna() | df_all['away_score'].isna()]
        
        df_completed.to_csv(self.data_dir / "nfl_results.csv", index=False)
        if len(df_scheduled) > 0:
            df_scheduled.to_csv(self.data_dir / "nfl_schedule.csv", index=False)
            
        logger.info(f"Exported {len(df_completed)} completed games and {len(df_scheduled)} scheduled games")

    def export_teams_to_json(self):
        """Export enhanced team information to JSON"""
        logger.info("Exporting enhanced team data to JSON...")
        
        # Get all NFL teams
        teams = self.db.query(Team).filter(Team.league == League.NFL).all()
        
        teams_data = {}
        
        for team in teams:
            # Get enhanced details
            details = NFL_TEAM_DETAILS.get(team.team_uid, {})
            
            # Calculate team stats
            home_games = self.db.query(Game).filter(
                Game.home_team_uid == team.team_uid,
                Game.home_score.isnot(None)
            ).all()
            
            away_games = self.db.query(Game).filter(
                Game.away_team_uid == team.team_uid,
                Game.away_score.isnot(None)
            ).all()
            
            total_games = len(home_games) + len(away_games)
            home_wins = sum(1 for g in home_games if (g.home_score or 0) > (g.away_score or 0))
            away_wins = sum(1 for g in away_games if (g.away_score or 0) > (g.home_score or 0))
            total_wins = home_wins + away_wins
            
            teams_data[team.team_uid] = {
                "team_uid": team.team_uid,
                "name": team.name,
                "league": team.league.value,
                "city": details.get("city", "Unknown"),
                "state": details.get("state", "Unknown"), 
                "division": details.get("division", "Unknown"),
                "founded": details.get("founded", None),
                "colors": details.get("colors", []),
                "head_coach": details.get("head_coach", "Unknown"),
                "stadium": {
                    "name": details.get("stadium_name", "Unknown"),
                    "capacity": details.get("stadium_capacity", None),
                    "surface": details.get("stadium_surface", "Unknown"),
                    "gps_coordinates": details.get("stadium_gps", {}),
                    "city": details.get("city", "Unknown"),
                    "state": details.get("state", "Unknown")
                },
                "stats": {
                    "total_games_played": total_games,
                    "total_wins": total_wins,
                    "total_losses": total_games - total_wins,
                    "win_percentage": round(total_wins / total_games, 3) if total_games > 0 else 0,
                    "home_record": {"wins": home_wins, "losses": len(home_games) - home_wins},
                    "away_record": {"wins": away_wins, "losses": len(away_games) - away_wins}
                },
                "last_updated": datetime.utcnow().isoformat()
            }
        
        # Export complete teams data
        with open(self.data_dir / "nfl_teams_complete.json", "w") as f:
            json.dump(teams_data, f, indent=2)
            
        logger.info(f"Exported {len(teams_data)} teams to nfl_teams_complete.json")
        
        # Export simplified teams lookup
        teams_lookup = {}
        for uid, data in teams_data.items():
            teams_lookup[data["name"]] = {
                "team_uid": uid,
                "city": data["city"],
                "division": data["division"],
                "stadium": data["stadium"]["name"]
            }
            
        with open(self.data_dir / "nfl_teams_lookup.json", "w") as f:
            json.dump(teams_lookup, f, indent=2)
            
        # Export stadiums data
        stadiums_data = {}
        for uid, data in teams_data.items():
            stadium_name = data["stadium"]["name"]
            if stadium_name not in stadiums_data:
                stadiums_data[stadium_name] = {
                    "name": stadium_name,
                    "capacity": data["stadium"]["capacity"],
                    "surface": data["stadium"]["surface"],
                    "gps_coordinates": data["stadium"]["gps_coordinates"],
                    "city": data["stadium"]["city"],
                    "state": data["stadium"]["state"],
                    "teams": []
                }
            stadiums_data[stadium_name]["teams"].append({
                "name": data["name"],
                "team_uid": uid
            })
            
        with open(self.data_dir / "nfl_stadiums.json", "w") as f:
            json.dump(stadiums_data, f, indent=2)
            
        logger.info(f"Exported {len(stadiums_data)} stadiums to nfl_stadiums.json")

    def export_stats_to_csv(self):
        """Export team and season statistics to CSV"""
        logger.info("Exporting statistics to CSV files...")
        
        # Team season stats
        teams = self.db.query(Team).filter(Team.league == League.NFL).all()
        team_stats = []
        
        for team in teams:
            for season in [2022, 2023, 2024]:
                # Get games for this team and season
                home_games = self.db.query(Game).filter(
                    Game.home_team_uid == team.team_uid,
                    Game.season == season,
                    Game.home_score.isnot(None)
                ).all()
                
                away_games = self.db.query(Game).filter(
                    Game.away_team_uid == team.team_uid,
                    Game.season == season,
                    Game.away_score.isnot(None)
                ).all()
                
                if not home_games and not away_games:
                    continue
                    
                total_games = len(home_games) + len(away_games)
                home_wins = sum(1 for g in home_games if (g.home_score or 0) > (g.away_score or 0))
                away_wins = sum(1 for g in away_games if (g.away_score or 0) > (g.home_score or 0))
                total_wins = home_wins + away_wins
                
                points_scored = sum((g.home_score or 0) for g in home_games) + sum((g.away_score or 0) for g in away_games)
                points_allowed = sum((g.away_score or 0) for g in home_games) + sum((g.home_score or 0) for g in away_games)
                
                team_stats.append({
                    "team_name": team.name,
                    "team_uid": team.team_uid,
                    "season": season,
                    "games_played": total_games,
                    "wins": total_wins,
                    "losses": total_games - total_wins,
                    "win_percentage": round(total_wins / total_games, 3) if total_games > 0 else 0,
                    "home_wins": home_wins,
                    "home_losses": len(home_games) - home_wins,
                    "away_wins": away_wins,
                    "away_losses": len(away_games) - away_wins,
                    "points_scored": points_scored,
                    "points_allowed": points_allowed,
                    "point_differential": points_scored - points_allowed,
                    "avg_points_scored": round(points_scored / total_games, 1) if total_games > 0 else 0,
                    "avg_points_allowed": round(points_allowed / total_games, 1) if total_games > 0 else 0
                })
        
        df_team_stats = pd.DataFrame(team_stats)
        df_team_stats.to_csv(self.data_dir / "nfl_team_season_stats.csv", index=False)
        logger.info(f"Exported team season statistics for {len(team_stats)} team-seasons")

    def export_all_data(self):
        """Export all data to structured files"""
        logger.info("Starting complete NFL data export...")
        
        self.export_games_to_csv()
        self.export_teams_to_json()
        self.export_stats_to_csv()
        
        # Create data summary
        summary = {
            "export_date": datetime.utcnow().isoformat(),
            "total_teams": self.db.query(Team).filter(Team.league == League.NFL).count(),
            "total_games": self.db.query(Game).filter(Game.league == League.NFL).count(),
            "seasons_covered": [2022, 2023, 2024],
            "files_created": [
                "nfl_games_complete.csv",
                "nfl_games_2022.csv", 
                "nfl_games_2023.csv",
                "nfl_games_2024.csv",
                "nfl_results.csv",
                "nfl_teams_complete.json",
                "nfl_teams_lookup.json",
                "nfl_stadiums.json",
                "nfl_team_season_stats.csv"
            ],
            "data_sources": ["pro_football_reference"],
            "description": "Complete NFL dataset with 3 seasons of games, enhanced team information, and stadium details",
            "data_notes": {
                "game_dates": "Dates are stored as YYYY-MM-DD format. Kickoff times are not available from Pro Football Reference, so only dates are provided.",
                "playoff_games": "Playoff games are categorized by type: regular, wildcard, divisional, conference, superbowl",
                "historical_data": "All data is historical through February 9, 2025 (2024 season Super Bowl)"
            }
        }
        
        with open(self.data_dir / "data_summary.json", "w") as f:
            json.dump(summary, f, indent=2)
            
        logger.info("=== DATA EXPORT COMPLETE ===")
        logger.info(f"All files saved to: {self.data_dir.absolute()}")
        for file in summary["files_created"]:
            logger.info(f"  - {file}")


def main():
    """Main export script"""
    try:
        with NFLDataExporter() as exporter:
            exporter.export_all_data()
            
    except Exception as e:
        logger.error(f"Error during data export: {e}")
        raise


if __name__ == "__main__":
    main()