#!/usr/bin/env python3
"""Complete NFL data scraper for 3 seasons (2022-2024) from Pro Football Reference"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.scrapers.pro_football_reference_fixed import ProFootballReferenceScraper
from backend.app.models import Team, Game, League
from backend.app.core.database import SessionLocal
import logging
from datetime import datetime
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Team name mapping from Pro Football Reference to our database
TEAM_NAME_MAPPING = {
    # AFC East
    "Buffalo Bills": "NFL_134918",
    "Miami Dolphins": "NFL_134919", 
    "New England Patriots": "NFL_134920",
    "New York Jets": "NFL_134921",
    
    # AFC North
    "Baltimore Ravens": "NFL_134922",
    "Cincinnati Bengals": "NFL_134923",
    "Cleveland Browns": "NFL_134924",
    "Pittsburgh Steelers": "NFL_134925",
    
    # AFC South
    "Houston Texans": "NFL_134926",
    "Indianapolis Colts": "NFL_134927",
    "Jacksonville Jaguars": "NFL_134928",
    "Tennessee Titans": "NFL_134929",
    
    # AFC West
    "Denver Broncos": "NFL_134930",
    "Kansas City Chiefs": "NFL_134931",
    "Las Vegas Raiders": "NFL_134932",
    "Los Angeles Chargers": "NFL_135908",
    
    # NFC East
    "Dallas Cowboys": "NFL_134934",
    "New York Giants": "NFL_134935",
    "Philadelphia Eagles": "NFL_134936",
    "Washington Commanders": "NFL_134937",
    
    # NFC North  
    "Chicago Bears": "NFL_134938",
    "Detroit Lions": "NFL_134939",
    "Green Bay Packers": "NFL_134940",
    "Minnesota Vikings": "NFL_134941",
    
    # NFC South
    "Atlanta Falcons": "NFL_134942",
    "Carolina Panthers": "NFL_134943", 
    "New Orleans Saints": "NFL_134944",
    "Tampa Bay Buccaneers": "NFL_134945",
    
    # NFC West
    "Arizona Cardinals": "NFL_134946",
    "Los Angeles Rams": "NFL_135907",
    "San Francisco 49ers": "NFL_134948",
    "Seattle Seahawks": "NFL_134949"
}


class CompleteNFLDataIngestion:
    def __init__(self):
        self.db = SessionLocal()
        self.scraper = None
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.scraper:
            self.scraper.close()
        self.db.close()
    
    def map_team_name(self, team_name: str) -> str:
        """Map Pro Football Reference team name to our team UID"""
        # Clean the team name
        team_name = team_name.strip()
        
        # Direct mapping first
        if team_name in TEAM_NAME_MAPPING:
            return TEAM_NAME_MAPPING[team_name]
        
        # Try fuzzy matching for variations
        for mapped_name, uid in TEAM_NAME_MAPPING.items():
            if mapped_name.lower() in team_name.lower() or team_name.lower() in mapped_name.lower():
                return uid
        
        # Handle special cases
        special_cases = {
            "Washington": "NFL_134937",  # Washington Football Team/Commanders
            "Washington Football Team": "NFL_134937",
            "Raiders": "NFL_134932",  # Las Vegas/Oakland Raiders
            "Chargers": "NFL_135908",  # Los Angeles/San Diego Chargers
            "Rams": "NFL_135907"      # Los Angeles/St. Louis Rams
        }
        
        for case, uid in special_cases.items():
            if case.lower() in team_name.lower():
                return uid
        
        logger.warning(f"Could not map team name: {team_name}")
        return None
    
    def transform_scraped_game(self, scraped_game: dict) -> dict:
        """Transform scraped game data to our database schema"""
        # Map team names to UIDs
        home_team_uid = self.map_team_name(scraped_game["home_team"])
        away_team_uid = self.map_team_name(scraped_game["away_team"])
        
        if not home_team_uid or not away_team_uid:
            raise ValueError(f"Could not map teams: {scraped_game['home_team']} vs {scraped_game['away_team']}")
        
        return {
            "game_uid": f"NFL_{scraped_game['game_id']}",
            "league": League.NFL,
            "season": scraped_game["season"],
            "week": scraped_game["week"],
            "home_team_uid": home_team_uid,
            "away_team_uid": away_team_uid,
            "game_datetime": scraped_game["date"],
            "home_score": scraped_game["home_score"],
            "away_score": scraped_game["away_score"],
            "source": "pro_football_reference"
        }
    
    def ingest_season_games(self, year: int) -> int:
        """Ingest all games for a specific season"""
        logger.info(f"Starting ingestion for {year} NFL season...")
        
        if not self.scraper:
            self.scraper = ProFootballReferenceScraper(headless=True)
        
        # Scrape the season
        games_data = self.scraper.scrape_season_schedule(year)
        logger.info(f"Scraped {len(games_data)} games for {year} season")
        
        added_count = 0
        updated_count = 0
        error_count = 0
        
        for scraped_game in games_data:
            try:
                # Transform to our schema
                game_data = self.transform_scraped_game(scraped_game)
                
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
                    logger.info(f"Progress: {added_count + updated_count} games processed for {year}")
                    
            except Exception as e:
                logger.warning(f"Error processing game {scraped_game.get('game_id', 'unknown')} for {year}: {e}")
                error_count += 1
                continue
        
        # Final commit for the season
        self.db.commit()
        logger.info(f"Season {year} completed! Added: {added_count}, Updated: {updated_count}, Errors: {error_count}")
        
        return added_count
    
    def run_complete_ingestion(self, years: list = [2022, 2023, 2024]):
        """Run complete NFL data ingestion for multiple seasons"""
        logger.info(f"Starting complete NFL data ingestion for seasons: {years}")
        
        total_added = 0
        
        for year in years:
            try:
                added = self.ingest_season_games(year)
                total_added += added
                
                # Be respectful to the server between seasons
                if year != years[-1]:  # Don't sleep after the last season
                    logger.info("Waiting between seasons...")
                    time.sleep(5)
                    
            except Exception as e:
                logger.error(f"Error processing {year} season: {e}")
                continue
        
        # Final summary
        self.get_final_summary()
        
        return total_added
    
    def get_final_summary(self):
        """Get final summary of ingested data"""
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
        
        logger.info("=== FINAL INGESTION SUMMARY ===")
        logger.info(f"Total NFL teams: {team_count}")
        logger.info(f"Total NFL games: {game_count}")
        logger.info("Games by season:")
        for season, count in sorted(season_counts.items()):
            logger.info(f"  {season}: {count} games")
            
        # Expected game counts (approximate)
        expected_counts = {
            2022: 285,  # 17 weeks * 16 games + playoffs
            2023: 285,
            2024: 285
        }
        
        logger.info("\nData completeness check:")
        for season, expected in expected_counts.items():
            actual = season_counts.get(season, 0)
            percentage = (actual / expected) * 100 if expected > 0 else 0
            logger.info(f"  {season}: {actual}/{expected} games ({percentage:.1f}% complete)")


def main():
    """Main ingestion script"""
    try:
        logger.info("Starting complete NFL data scraping from Pro Football Reference")
        logger.info("This will scrape 3 full seasons (2022-2024) - approximately 850+ games")
        
        with CompleteNFLDataIngestion() as ingestion:
            total_games = ingestion.run_complete_ingestion([2022, 2023, 2024])
            
            logger.info("=== SCRAPING COMPLETE ===")
            logger.info(f"Successfully added {total_games} new games to the database")
            logger.info("The Sports Data Aggregator now has complete 3-season NFL data!")
            
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error during scraping: {e}")
        raise


if __name__ == "__main__":
    main()