#!/usr/bin/env python3
"""Complete NFL data ingestion for teams, games, and players from 2022-2024"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.ingestion.thesportsdb import TheSportsDBClient
from backend.app.models import Team, Game, Player, PlayerStat, League
from backend.app.core.database import SessionLocal
import logging
from datetime import datetime, timedelta
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class NFLDataIngestion:
    def __init__(self):
        self.client = TheSportsDBClient()
        self.db = SessionLocal()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
        self.db.close()
    
    def ingest_all_teams(self):
        """Ingest all NFL teams"""
        logger.info("Starting NFL teams ingestion...")
        
        try:
            teams_data = self.client.get_all_teams("NFL")
            logger.info(f"Found {len(teams_data)} NFL teams from API")
            
            added_count = 0
            updated_count = 0
            
            for tsdb_team in teams_data:
                team_data = self.client.transform_team_data(tsdb_team, League.NFL)
                
                # Check if team already exists
                existing_team = self.db.query(Team).filter(Team.team_uid == team_data["team_uid"]).first()
                
                if existing_team:
                    # Update existing team
                    for field, value in team_data.items():
                        if field not in ['team_uid', 'created_at']:
                            setattr(existing_team, field, value)
                    existing_team.updated_at = datetime.utcnow()
                    updated_count += 1
                    logger.info(f"Updated team: {existing_team.name}")
                else:
                    # Create new team
                    team = Team(**team_data)
                    self.db.add(team)
                    added_count += 1
                    logger.info(f"Added team: {team.name}")
            
            self.db.commit()
            logger.info(f"Teams ingestion completed! Added: {added_count}, Updated: {updated_count}")
            
        except Exception as e:
            logger.error(f"Error during teams ingestion: {e}")
            self.db.rollback()
            raise
    
    def ingest_season_schedule(self, season: str):
        """Ingest games for a specific season"""
        logger.info(f"Starting NFL {season} season schedule ingestion...")
        
        try:
            # Get schedule data for the season
            schedule_data = self.client.get_schedule("4391", season)  # 4391 is NFL league ID
            logger.info(f"Found {len(schedule_data)} games for {season} season")
            
            added_count = 0
            updated_count = 0
            
            for tsdb_event in schedule_data:
                try:
                    game_data = self.client.transform_game_data(tsdb_event, League.NFL)
                    
                    # Check if game already exists
                    existing_game = self.db.query(Game).filter(Game.game_uid == game_data["game_uid"]).first()
                    
                    if existing_game:
                        # Update existing game
                        for field, value in game_data.items():
                            if field not in ['game_uid', 'created_at']:
                                setattr(existing_game, field, value)
                        existing_game.updated_at = datetime.utcnow()
                        updated_count += 1
                        logger.debug(f"Updated game: {existing_game.game_uid}")
                    else:
                        # Create new game
                        game = Game(**game_data)
                        self.db.add(game)
                        added_count += 1
                        logger.debug(f"Added game: {game.game_uid}")
                    
                    # Commit in batches to avoid memory issues
                    if (added_count + updated_count) % 50 == 0:
                        self.db.commit()
                        logger.info(f"Progress: {added_count + updated_count} games processed")
                        
                except Exception as e:
                    logger.warning(f"Error processing game {tsdb_event.get('idEvent', 'unknown')}: {e}")
                    continue
            
            self.db.commit()
            logger.info(f"Season {season} ingestion completed! Added: {added_count}, Updated: {updated_count}")
            
        except Exception as e:
            logger.error(f"Error during {season} season ingestion: {e}")
            self.db.rollback()
            raise
    
    def ingest_team_players(self, team_uid: str, team_name: str):
        """Ingest players for a specific team"""
        logger.info(f"Starting player ingestion for {team_name}...")
        
        try:
            # Extract team ID from team_uid (format: NFL_134918)
            team_id = team_uid.split('_')[1]
            players_data = self.client.get_players_by_team(team_id)
            
            if not players_data:
                logger.warning(f"No players found for {team_name}")
                return
            
            logger.info(f"Found {len(players_data)} players for {team_name}")
            
            added_count = 0
            updated_count = 0
            
            for tsdb_player in players_data:
                try:
                    player_data = self.client.transform_player_data(tsdb_player, team_uid)
                    
                    # Check if player already exists
                    existing_player = self.db.query(Player).filter(Player.player_uid == player_data["player_uid"]).first()
                    
                    if existing_player:
                        # Update existing player
                        for field, value in player_data.items():
                            if field not in ['player_uid', 'created_at']:
                                setattr(existing_player, field, value)
                        existing_player.updated_at = datetime.utcnow()
                        updated_count += 1
                    else:
                        # Create new player
                        player = Player(**player_data)
                        self.db.add(player)
                        added_count += 1
                    
                except Exception as e:
                    logger.warning(f"Error processing player {tsdb_player.get('idPlayer', 'unknown')}: {e}")
                    continue
            
            self.db.commit()
            logger.info(f"Players for {team_name} completed! Added: {added_count}, Updated: {updated_count}")
            
        except Exception as e:
            logger.error(f"Error during player ingestion for {team_name}: {e}")
            self.db.rollback()
    
    def ingest_all_players(self):
        """Ingest players for all NFL teams"""
        logger.info("Starting comprehensive NFL players ingestion...")
        
        teams = self.db.query(Team).filter(Team.league == League.NFL).all()
        logger.info(f"Found {len(teams)} NFL teams to process for players")
        
        for i, team in enumerate(teams, 1):
            logger.info(f"Processing team {i}/{len(teams)}: {team.name}")
            self.ingest_team_players(team.team_uid, team.name)
            
            # Rate limiting - be respectful to the API
            time.sleep(1)
    
    def run_complete_ingestion(self):
        """Run complete NFL data ingestion for the past 3 seasons"""
        logger.info("Starting complete NFL data ingestion (2022-2024)")
        
        # Step 1: Ingest all teams
        self.ingest_all_teams()
        
        # Step 2: Ingest games for each season
        seasons = ["2022-2023", "2023-2024", "2024-2025"]
        for season in seasons:
            self.ingest_season_schedule(season)
            time.sleep(2)  # Rate limiting between seasons
        
        # Step 3: Ingest players for all teams
        self.ingest_all_players()
        
        # Final summary
        team_count = self.db.query(Team).filter(Team.league == League.NFL).count()
        game_count = self.db.query(Game).filter(Game.league == League.NFL).count()
        player_count = self.db.query(Player).count()
        
        logger.info("=== INGESTION COMPLETE ===")
        logger.info(f"Total NFL teams: {team_count}")
        logger.info(f"Total NFL games: {game_count}")
        logger.info(f"Total players: {player_count}")


def main():
    """Main ingestion script"""
    try:
        with NFLDataIngestion() as ingestion:
            ingestion.run_complete_ingestion()
            
    except KeyboardInterrupt:
        logger.info("Ingestion interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error during ingestion: {e}")
        raise


if __name__ == "__main__":
    main()