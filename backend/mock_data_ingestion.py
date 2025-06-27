#!/usr/bin/env python3
"""Mock data ingestion for testing purposes"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.models import Team, Game, Player, PlayerStat, League
from backend.app.core.database import SessionLocal
from datetime import datetime, timedelta
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Mock NFL teams data
NFL_TEAMS = [
    {"city": "Dallas", "name": "Cowboys", "abbreviation": "DAL", "conference": "NFC", "division": "East"},
    {"city": "New England", "name": "Patriots", "abbreviation": "NE", "conference": "AFC", "division": "East"},
    {"city": "Green Bay", "name": "Packers", "abbreviation": "GB", "conference": "NFC", "division": "North"},
    {"city": "Kansas City", "name": "Chiefs", "abbreviation": "KC", "conference": "AFC", "division": "West"},
    {"city": "San Francisco", "name": "49ers", "abbreviation": "SF", "conference": "NFC", "division": "West"},
    {"city": "Buffalo", "name": "Bills", "abbreviation": "BUF", "conference": "AFC", "division": "East"},
    {"city": "Philadelphia", "name": "Eagles", "abbreviation": "PHI", "conference": "NFC", "division": "East"},
    {"city": "Cincinnati", "name": "Bengals", "abbreviation": "CIN", "conference": "AFC", "division": "North"},
]


def create_mock_teams(db):
    """Create mock NFL teams"""
    logger.info("Creating mock NFL teams...")
    
    for team_data in NFL_TEAMS:
        team_uid = f"NFL_{team_data['abbreviation']}"
        
        # Check if exists
        existing = db.query(Team).filter(Team.team_uid == team_uid).first()
        if existing:
            continue
            
        team = Team(
            team_uid=team_uid,
            league=League.NFL,
            city=team_data["city"],
            name=team_data["name"],
            abbreviation=team_data["abbreviation"],
            conference=team_data["conference"],
            division=team_data["division"],
            stadium_capacity=random.randint(65000, 85000),
            source="mock_data"
        )
        db.add(team)
        logger.info(f"Added team: {team.city} {team.name}")
    
    db.commit()


def create_mock_games(db):
    """Create mock games for current NFL season"""
    logger.info("Creating mock NFL games...")
    
    teams = db.query(Team).filter(Team.league == League.NFL).all()
    if len(teams) < 2:
        logger.error("Need at least 2 teams to create games")
        return
    
    # Create some games for week 1
    base_date = datetime(2023, 9, 7, 20, 0, 0)  # Thursday Night Football
    
    for i in range(min(4, len(teams) // 2)):
        home_team = teams[i * 2]
        away_team = teams[i * 2 + 1]
        
        game_uid = f"NFL_2023_W1_G{i+1}"
        
        # Check if exists
        existing = db.query(Game).filter(Game.game_uid == game_uid).first()
        if existing:
            continue
        
        game = Game(
            game_uid=game_uid,
            league=League.NFL,
            season=2023,
            week=1,
            game_type="regular",
            home_team_uid=home_team.team_uid,
            away_team_uid=away_team.team_uid,
            game_datetime=base_date + timedelta(days=i if i < 3 else 3, hours=i * 3 if i < 3 else 0),
            venue=f"{home_team.city} Stadium",
            home_score=random.randint(14, 35),
            away_score=random.randint(14, 35),
            attendance=random.randint(65000, 75000),
            source="mock_data"
        )
        db.add(game)
        logger.info(f"Added game: {away_team.city} @ {home_team.city}")
    
    db.commit()


def create_mock_players(db):
    """Create mock players"""
    logger.info("Creating mock NFL players...")
    
    teams = db.query(Team).filter(Team.league == League.NFL).all()
    
    positions = ["QB", "RB", "WR", "TE", "OL", "DL", "LB", "CB", "S"]
    first_names = ["Tom", "Patrick", "Josh", "Dak", "Travis", "Nick", "Aaron", "Justin"]
    last_names = ["Brady", "Mahomes", "Allen", "Prescott", "Kelce", "Bosa", "Donald", "Jefferson"]
    
    for team in teams[:4]:  # Just first 4 teams for now
        for i in range(5):  # 5 players per team
            player_uid = f"PLAYER_{team.abbreviation}_{i+1}"
            
            # Check if exists
            existing = db.query(Player).filter(Player.player_uid == player_uid).first()
            if existing:
                continue
            
            player = Player(
                player_uid=player_uid,
                name=f"{random.choice(first_names)} {random.choice(last_names)}",
                position=random.choice(positions),
                jersey_number=random.randint(1, 99),
                team_uid=team.team_uid,
                height_inches=random.randint(68, 78),
                weight_lbs=random.randint(180, 320),
                source="mock_data"
            )
            db.add(player)
            logger.info(f"Added player: {player.name} ({team.abbreviation})")
    
    db.commit()


def main():
    """Run mock data ingestion"""
    db = SessionLocal()
    
    try:
        create_mock_teams(db)
        create_mock_games(db)
        create_mock_players(db)
        
        # Display summary
        team_count = db.query(Team).filter(Team.league == League.NFL).count()
        game_count = db.query(Game).filter(Game.league == League.NFL).count()
        player_count = db.query(Player).count()
        
        logger.info(f"\nMock data ingestion complete!")
        logger.info(f"Total NFL teams: {team_count}")
        logger.info(f"Total NFL games: {game_count}")
        logger.info(f"Total players: {player_count}")
        
    except Exception as e:
        logger.error(f"Error during mock ingestion: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()