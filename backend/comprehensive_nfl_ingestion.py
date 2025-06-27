#!/usr/bin/env python3
"""Comprehensive NFL data ingestion for teams and games"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.ingestion.thesportsdb import TheSportsDBClient
from backend.app.models import Team, Game, League
from backend.app.core.database import SessionLocal
import logging
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ComprehensiveNFLIngestion:
    def __init__(self):
        self.client = TheSportsDBClient()
        self.db = SessionLocal()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
        self.db.close()
    
    def ingest_team_games(self, team_uid: str, team_name: str):
        """Ingest games for a specific team"""
        logger.info(f"Fetching games for {team_name}...")
        
        try:
            # Extract team ID from team_uid (format: NFL_134918)
            team_id = team_uid.split('_')[1]
            games_data = self.client.get_past_events(team_id, limit=50)  # Get up to 50 games
            
            if not games_data:
                logger.warning(f"No games found for {team_name}")
                return 0, 0
            
            logger.info(f"Found {len(games_data)} games for {team_name}")
            
            added_count = 0
            updated_count = 0
            
            for tsdb_event in games_data:
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
                    else:
                        # Create new game
                        game = Game(**game_data)
                        self.db.add(game)
                        added_count += 1
                    
                except Exception as e:
                    logger.warning(f"Error processing game {tsdb_event.get('idEvent', 'unknown')} for {team_name}: {e}")
                    continue
            
            # Commit changes for this team
            self.db.commit()
            logger.info(f"Games for {team_name} completed! Added: {added_count}, Updated: {updated_count}")
            return added_count, updated_count
            
        except Exception as e:
            logger.error(f"Error during game ingestion for {team_name}: {e}")
            self.db.rollback()
            return 0, 0
    
    def ingest_all_team_games(self):
        """Ingest games for all NFL teams"""
        logger.info("Starting comprehensive NFL games ingestion...")
        
        teams = self.db.query(Team).filter(Team.league == League.NFL).all()
        logger.info(f"Found {len(teams)} NFL teams to process for games")
        
        total_added = 0
        total_updated = 0
        
        for i, team in enumerate(teams, 1):
            logger.info(f"Processing team {i}/{len(teams)}: {team.name}")
            added, updated = self.ingest_team_games(team.team_uid, team.name)
            total_added += added
            total_updated += updated
            
            # Rate limiting - be respectful to the API
            time.sleep(2)
            
            # Progress update every 5 teams
            if i % 5 == 0:
                current_count = self.db.query(Game).filter(Game.league == League.NFL).count()
                logger.info(f"Progress update: {i}/{len(teams)} teams processed, {current_count} total games in database")
        
        logger.info(f"All team games ingestion completed! Total added: {total_added}, Total updated: {total_updated}")
        
    def get_ingestion_summary(self):
        """Get summary of current data"""
        team_count = self.db.query(Team).filter(Team.league == League.NFL).count()
        game_count = self.db.query(Game).filter(Game.league == League.NFL).count()
        
        # Get games by season
        seasons = self.db.query(Game.season).filter(Game.league == League.NFL).distinct().all()
        season_counts = {}
        for season_tuple in seasons:
            season = season_tuple[0]
            if season:
                count = self.db.query(Game).filter(Game.league == League.NFL, Game.season == season).count()
                season_counts[season] = count
        
        logger.info("=== INGESTION SUMMARY ===")
        logger.info(f"Total NFL teams: {team_count}")
        logger.info(f"Total NFL games: {game_count}")
        logger.info("Games by season:")
        for season, count in sorted(season_counts.items()):
            logger.info(f"  {season}: {count} games")
        
        return {
            "teams": team_count,
            "games": game_count,
            "seasons": season_counts
        }
    
    def run_comprehensive_ingestion(self):
        """Run comprehensive NFL data ingestion"""
        logger.info("Starting comprehensive NFL data ingestion")
        
        # We already have teams, so just ingest games from all teams
        self.ingest_all_team_games()
        
        # Get final summary
        summary = self.get_ingestion_summary()
        
        return summary


def main():
    """Main ingestion script"""
    try:
        with ComprehensiveNFLIngestion() as ingestion:
            summary = ingestion.run_comprehensive_ingestion()
            
            logger.info("=== FINAL RESULTS ===")
            logger.info(f"Successfully ingested data for {summary['teams']} teams")
            logger.info(f"Total games in database: {summary['games']}")
            
    except KeyboardInterrupt:
        logger.info("Ingestion interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error during ingestion: {e}")
        raise


if __name__ == "__main__":
    main()