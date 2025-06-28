#!/usr/bin/env python3
"""Comprehensive scraper for detailed NFL game data from Pro Football Reference"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backend.boxscore_scraper import BoxscoreScraper
from backend.app.core.database import SessionLocal
from backend.app.models import Game, League
import logging
import json
import time
import re
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DetailedGameDataScraper:
    """Scraper for collecting detailed game data and storing as structured files"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.scraper = None
        self.data_dir = Path("detailed_game_data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for organized storage
        (self.data_dir / "boxscores").mkdir(exist_ok=True)
        (self.data_dir / "team_stats").mkdir(exist_ok=True)
        (self.data_dir / "player_stats").mkdir(exist_ok=True)
        (self.data_dir / "expected_points").mkdir(exist_ok=True)
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.scraper:
            self.scraper.close()
        self.db.close()
    
    def scrape_detailed_data_for_season(self, season: int, max_games: int = None):
        """Scrape detailed data for all games in a season"""
        logger.info(f"Starting detailed data scraping for {season} season")
        
        # Get games for the season
        games_query = self.db.query(Game).filter(
            Game.league == League.NFL,
            Game.season == season,
            Game.source == 'pro_football_reference'
        )
        
        if max_games:
            games_query = games_query.limit(max_games)
            
        games = games_query.all()
        logger.info(f"Found {len(games)} games to scrape for {season}")
        
        if not self.scraper:
            self.scraper = BoxscoreScraper(headless=True)
        
        successfully_scraped = 0
        failed_scrapes = 0
        
        for i, game in enumerate(games, 1):
            try:
                logger.info(f"Scraping game {i}/{len(games)}: {game.game_uid}")
                logger.info(f"  {game.away_team.name if game.away_team else 'Unknown'} @ {game.home_team.name if game.home_team else 'Unknown'}")
                
                # Check if we already have this data
                boxscore_file = self.data_dir / "boxscores" / f"{game.game_uid}.json"
                if boxscore_file.exists():
                    logger.info(f"  ✅ Skipping - already exists")
                    continue
                
                # Scrape detailed boxscore data
                boxscore_data = self.scraper.scrape_detailed_boxscore(game.game_uid)
                
                if boxscore_data:
                    # Save complete boxscore data
                    with open(boxscore_file, 'w') as f:
                        json.dump(boxscore_data, f, indent=2)
                    
                    # Extract and save specific data types
                    self._save_extracted_data(game, boxscore_data)
                    
                    successfully_scraped += 1
                    logger.info(f"  ✅ Successfully scraped and saved")
                    
                else:
                    failed_scrapes += 1
                    logger.warning(f"  ❌ Failed to scrape data")
                
                # Be respectful to the server
                time.sleep(3)
                
                # Progress update every 10 games
                if i % 10 == 0:
                    logger.info(f"Progress: {i}/{len(games)} games processed")
                    
            except Exception as e:
                logger.error(f"Error scraping game {game.game_uid}: {e}")
                failed_scrapes += 1
                continue
        
        logger.info(f"Season {season} scraping complete!")
        logger.info(f"  Successfully scraped: {successfully_scraped}")
        logger.info(f"  Failed: {failed_scrapes}")
        logger.info(f"  Total: {len(games)}")
        
        return successfully_scraped, failed_scrapes
    
    def _save_extracted_data(self, game: Game, boxscore_data: dict):
        """Extract and save specific data types to organized files"""
        
        game_info = {
            "game_id": game.game_uid,
            "season": game.season,
            "week": game.week,
            "game_type": game.game_type,
            "date": game.game_datetime.date().isoformat() if game.game_datetime else None,
            "home_team": game.home_team.name if game.home_team else None,
            "away_team": game.away_team.name if game.away_team else None,
            "home_team_uid": game.home_team_uid,
            "away_team_uid": game.away_team_uid,
            "home_score": game.home_score,
            "away_score": game.away_score
        }
        
        # Save team stats
        team_stats = boxscore_data.get('team_stats', {})
        if team_stats:
            team_stats_data = {
                **game_info,
                "team_stats": team_stats,
                "scraped_at": datetime.utcnow().isoformat()
            }
            
            team_stats_file = self.data_dir / "team_stats" / f"{game.game_uid}_team_stats.json"
            with open(team_stats_file, 'w') as f:
                json.dump(team_stats_data, f, indent=2)
        
        # Save expected points data
        expected_points = team_stats.get('expected_points', [])
        if expected_points:
            ep_data = {
                **game_info,
                "expected_points": expected_points,
                "scraped_at": datetime.utcnow().isoformat()
            }
            
            ep_file = self.data_dir / "expected_points" / f"{game.game_uid}_expected_points.json"
            with open(ep_file, 'w') as f:
                json.dump(ep_data, f, indent=2)
        
        # Save player stats
        player_stats = boxscore_data.get('player_stats', {})
        if player_stats:
            player_data = {
                **game_info,
                "player_stats": player_stats,
                "scraped_at": datetime.utcnow().isoformat()
            }
            
            player_file = self.data_dir / "player_stats" / f"{game.game_uid}_player_stats.json"
            with open(player_file, 'w') as f:
                json.dump(player_data, f, indent=2)
    
    def create_summary_csvs(self):
        """Create summary CSV files from the scraped JSON data"""
        logger.info("Creating summary CSV files from scraped data")
        
        import pandas as pd
        
        # Create team stats summary
        team_stats_files = list((self.data_dir / "team_stats").glob("*.json"))
        if team_stats_files:
            team_data = []
            
            for file in team_stats_files:
                with open(file) as f:
                    data = json.load(f)
                    
                # Extract basic game info
                base_row = {
                    "game_id": data.get("game_id"),
                    "season": data.get("season"),
                    "week": data.get("week"),
                    "game_type": data.get("game_type"),
                    "date": data.get("date"),
                    "home_team": data.get("home_team"),
                    "away_team": data.get("away_team")
                }
                
                # Add expected points if available
                ep_data = data.get("team_stats", {}).get("expected_points", [])
                if ep_data and len(ep_data) >= 2:
                    away_ep = ep_data[1] if ep_data[1].get("") != data.get("home_team") else ep_data[0]
                    home_ep = ep_data[0] if ep_data[0].get("") == data.get("home_team") else ep_data[1]
                    
                    base_row.update({
                        "home_expected_points_offense": home_ep.get("Offense"),
                        "home_expected_points_defense": home_ep.get("Defense"),
                        "home_expected_points_special_teams": home_ep.get("Special Teams"),
                        "away_expected_points_offense": away_ep.get("Offense"),
                        "away_expected_points_defense": away_ep.get("Defense"),
                        "away_expected_points_special_teams": away_ep.get("Special Teams")
                    })
                
                team_data.append(base_row)
            
            if team_data:
                df = pd.DataFrame(team_data)
                df.to_csv(self.data_dir / "team_stats_summary.csv", index=False)
                logger.info(f"Created team_stats_summary.csv with {len(df)} games")
        
        # Create game summary with all basic stats
        boxscore_files = list((self.data_dir / "boxscores").glob("*.json"))
        if boxscore_files:
            game_summary = []
            
            for file in boxscore_files:
                with open(file) as f:
                    data = json.load(f)
                    
                # Extract game info and stats
                game_info = data.get("game_info", {})
                venue_info = game_info.get("venue", "")
                
                # Parse venue info for attendance, duration, etc.
                attendance = None
                duration = None
                if "Attendance:" in venue_info:
                    att_match = re.search(r"Attendance: ([\\d,]+)", venue_info)
                    if att_match:
                        attendance = int(att_match.group(1).replace(",", ""))
                if "Time of Game:" in venue_info:
                    dur_match = re.search(r"Time of Game: ([\\d:]+)", venue_info)
                    if dur_match:
                        duration = dur_match.group(1)
                
                summary_row = {
                    "game_id": data.get("game_id"),
                    "venue_info": venue_info,
                    "attendance": attendance,
                    "game_duration": duration,
                    "scoring_plays": len(data.get("scoring_summary", [])),
                    "team_stats_sections": len(data.get("team_stats", {})),
                    "player_stats_sections": len(data.get("player_stats", {}))
                }
                
                game_summary.append(summary_row)
            
            if game_summary:
                df = pd.DataFrame(game_summary)
                df.to_csv(self.data_dir / "detailed_games_summary.csv", index=False)
                logger.info(f"Created detailed_games_summary.csv with {len(df)} games")
    
    def get_scraping_status(self) -> dict:
        """Get status of what's been scraped"""
        boxscore_files = list((self.data_dir / "boxscores").glob("*.json"))
        team_stats_files = list((self.data_dir / "team_stats").glob("*.json"))
        player_stats_files = list((self.data_dir / "player_stats").glob("*.json"))
        ep_files = list((self.data_dir / "expected_points").glob("*.json"))
        
        # Get games by season from database
        seasons_data = {}
        for season in [2022, 2023, 2024]:
            total_games = self.db.query(Game).filter(
                Game.league == League.NFL,
                Game.season == season,
                Game.source == 'pro_football_reference'
            ).count()
            
            scraped_games = len([f for f in boxscore_files if f"_{season}_" in f.name or f.name.startswith(f"NFL_{season}")])
            
            seasons_data[season] = {
                "total_games": total_games,
                "scraped_games": scraped_games,
                "completion_rate": f"{(scraped_games/total_games)*100:.1f}%" if total_games > 0 else "0%"
            }
        
        return {
            "total_boxscores": len(boxscore_files),
            "total_team_stats": len(team_stats_files),
            "total_player_stats": len(player_stats_files),
            "total_expected_points": len(ep_files),
            "seasons": seasons_data,
            "data_directory": str(self.data_dir.absolute())
        }


def main():
    """Main function to run detailed game data scraping"""
    try:
        with DetailedGameDataScraper() as scraper:
            
            # Get current status
            status = scraper.get_scraping_status()
            logger.info("=== CURRENT SCRAPING STATUS ===")
            logger.info(f"Total boxscores: {status['total_boxscores']}")
            logger.info(f"Data directory: {status['data_directory']}")
            
            for season, data in status['seasons'].items():
                logger.info(f"{season}: {data['scraped_games']}/{data['total_games']} games ({data['completion_rate']})")
            
            # Ask user which season to scrape
            print("\\nWhich season would you like to scrape detailed data for?")
            print("1. 2024 season (most recent)")
            print("2. 2023 season") 
            print("3. 2022 season")
            print("4. All seasons")
            print("5. Just create summary CSVs from existing data")
            
            choice = input("Enter your choice (1-5): ").strip()
            
            if choice == "1":
                scraper.scrape_detailed_data_for_season(2024, max_games=10)  # Start with 10 games for testing
            elif choice == "2":
                scraper.scrape_detailed_data_for_season(2023, max_games=10)
            elif choice == "3":
                scraper.scrape_detailed_data_for_season(2022, max_games=10)
            elif choice == "4":
                for season in [2022, 2023, 2024]:
                    scraper.scrape_detailed_data_for_season(season, max_games=10)
            elif choice == "5":
                pass  # Just create CSVs
            else:
                logger.info("Invalid choice, creating summary CSVs only")
            
            # Create summary CSV files
            scraper.create_summary_csvs()
            
            # Final status
            final_status = scraper.get_scraping_status()
            logger.info("\\n=== FINAL STATUS ===")
            logger.info(f"Total boxscores: {final_status['total_boxscores']}")
            for season, data in final_status['seasons'].items():
                logger.info(f"{season}: {data['scraped_games']}/{data['total_games']} games ({data['completion_rate']})")
                
    except Exception as e:
        logger.error(f"Error during detailed scraping: {e}")
        raise


if __name__ == "__main__":
    main()