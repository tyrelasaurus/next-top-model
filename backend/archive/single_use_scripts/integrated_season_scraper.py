#!/usr/bin/env python3
"""Integrated NFL Season Data Scraper - Complete workflow for season data collection"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.scrapers.pro_football_reference_fixed import ProFootballReferenceScraper
from backend.boxscore_scraper import BoxscoreScraper
from backend.app.core.database import SessionLocal
from backend.app.models import Game, League, Team
import logging
import json
import time
import pandas as pd
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntegratedSeasonScraper:
    """Complete NFL season data scraping workflow"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.schedule_scraper = None
        self.boxscore_scraper = None
        self.data_dir = Path("season_data")
        self.data_dir.mkdir(exist_ok=True)
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.schedule_scraper:
            self.schedule_scraper.close()
        if self.boxscore_scraper:
            self.boxscore_scraper.close()
        self.db.close()
    
    def get_available_seasons(self) -> dict:
        """Get available seasons and their data status"""
        seasons_info = {}
        
        for season in [2022, 2023, 2024]:
            # Count games in database
            total_games = self.db.query(Game).filter(
                Game.league == League.NFL,
                Game.season == season,
                Game.source == 'pro_football_reference'
            ).count()
            
            # Check for detailed data
            detailed_data_dir = self.data_dir / f"season_{season}" / "boxscores"
            detailed_games = len(list(detailed_data_dir.glob("*.json"))) if detailed_data_dir.exists() else 0
            
            seasons_info[season] = {
                "total_games": total_games,
                "detailed_games": detailed_games,
                "completion_rate": f"{(detailed_games/total_games)*100:.1f}%" if total_games > 0 else "0%"
            }
            
        return seasons_info
    
    def validate_season_data(self, season: int) -> dict:
        """Validate that season data exists and is complete"""
        logger.info(f"Validating season {season} data...")
        
        # Get all games for the season
        games = self.db.query(Game).filter(
            Game.league == League.NFL,
            Game.season == season,
            Game.source == 'pro_football_reference'
        ).all()
        
        validation_results = {
            "total_games": len(games),
            "games_with_results": 0,
            "games_missing_teams": 0,
            "duplicate_game_ids": [],
            "games_by_type": {},
            "date_range": {"earliest": None, "latest": None}
        }
        
        game_ids_seen = set()
        
        for game in games:
            # Check for results
            if game.home_score is not None and game.away_score is not None:
                validation_results["games_with_results"] += 1
            
            # Check for team assignments
            if not game.home_team_uid or not game.away_team_uid:
                validation_results["games_missing_teams"] += 1
            
            # Check for duplicates
            if game.game_uid in game_ids_seen:
                validation_results["duplicate_game_ids"].append(game.game_uid)
            else:
                game_ids_seen.add(game.game_uid)
            
            # Count by game type
            game_type = game.game_type or "unknown"
            validation_results["games_by_type"][game_type] = validation_results["games_by_type"].get(game_type, 0) + 1
            
            # Track date range
            if game.game_datetime:
                game_date = game.game_datetime.date()
                if not validation_results["date_range"]["earliest"] or game_date < validation_results["date_range"]["earliest"]:
                    validation_results["date_range"]["earliest"] = game_date
                if not validation_results["date_range"]["latest"] or game_date > validation_results["date_range"]["latest"]:
                    validation_results["date_range"]["latest"] = game_date
        
        # Convert dates to strings for JSON serialization
        if validation_results["date_range"]["earliest"]:
            validation_results["date_range"]["earliest"] = validation_results["date_range"]["earliest"].isoformat()
        if validation_results["date_range"]["latest"]:
            validation_results["date_range"]["latest"] = validation_results["date_range"]["latest"].isoformat()
        
        return validation_results
    
    def scrape_complete_season(self, season: int, force_refresh: bool = False, max_detailed_games: int = None):
        """Complete workflow: validate schedule, scrape detailed data, export results"""
        logger.info(f"Starting complete season scrape for {season}")
        
        # Create season-specific directory
        season_dir = self.data_dir / f"season_{season}"
        season_dir.mkdir(exist_ok=True)
        
        # Step 1: Validate existing schedule data
        logger.info("Step 1: Validating schedule data...")
        validation = self.validate_season_data(season)
        
        with open(season_dir / "validation_report.json", 'w') as f:
            json.dump(validation, f, indent=2)
        
        logger.info(f"Season {season} validation:")
        logger.info(f"  Total games: {validation['total_games']}")
        logger.info(f"  Games with results: {validation['games_with_results']}")
        logger.info(f"  Games by type: {validation['games_by_type']}")
        
        if validation["duplicate_game_ids"]:
            logger.warning(f"  Found {len(validation['duplicate_game_ids'])} duplicate game IDs")
        
        # Step 2: Export schedule to CSV
        logger.info("Step 2: Exporting schedule data...")
        self._export_season_schedule(season, season_dir)
        
        # Step 3: Scrape detailed boxscore data
        logger.info("Step 3: Scraping detailed game data...")
        detailed_results = self._scrape_detailed_season_data(season, season_dir, max_detailed_games)
        
        # Step 4: Create comprehensive summary
        logger.info("Step 4: Creating summary reports...")
        self._create_season_summary(season, season_dir, validation, detailed_results)
        
        logger.info(f"Complete season {season} scraping finished!")
        logger.info(f"Data saved to: {season_dir.absolute()}")
        
        return {
            "season": season,
            "validation": validation,
            "detailed_results": detailed_results,
            "data_directory": str(season_dir.absolute())
        }
    
    def _export_season_schedule(self, season: int, season_dir: Path):
        """Export season schedule to CSV"""
        games = self.db.query(Game).filter(
            Game.league == League.NFL,
            Game.season == season,
            Game.source == 'pro_football_reference'
        ).order_by(Game.game_datetime).all()
        
        schedule_data = []
        for game in games:
            # Format datetime properly
            game_date = None
            game_time = None
            
            if game.game_datetime:
                # Show just date if we don't have real kickoff time (fake 12:00:00 timestamps)
                if game.game_datetime.hour == 12 and game.game_datetime.minute == 0:
                    game_date = game.game_datetime.date().isoformat()
                else:
                    game_date = game.game_datetime.date().isoformat()
                    game_time = game.game_datetime.time().isoformat()
            
            schedule_data.append({
                "game_id": game.game_uid,
                "season": game.season,
                "week": game.week,
                "game_type": game.game_type,
                "date": game_date,
                "time": game_time,
                "home_team": game.home_team.name if game.home_team else None,
                "away_team": game.away_team.name if game.away_team else None,
                "home_team_uid": game.home_team_uid,
                "away_team_uid": game.away_team_uid,
                "home_score": game.home_score,
                "away_score": game.away_score,
                "source": game.source
            })
        
        df = pd.DataFrame(schedule_data)
        df.to_csv(season_dir / f"schedule_{season}.csv", index=False)
        logger.info(f"Exported {len(schedule_data)} games to schedule_{season}.csv")
    
    def _scrape_detailed_season_data(self, season: int, season_dir: Path, max_games: int = None):
        """Scrape detailed boxscore data for all games in season"""
        
        # Create subdirectories
        boxscores_dir = season_dir / "boxscores"
        team_stats_dir = season_dir / "team_stats" 
        player_stats_dir = season_dir / "player_stats"
        expected_points_dir = season_dir / "expected_points"
        
        for dir_path in [boxscores_dir, team_stats_dir, player_stats_dir, expected_points_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Get games to scrape
        games_query = self.db.query(Game).filter(
            Game.league == League.NFL,
            Game.season == season,
            Game.source == 'pro_football_reference'
        ).order_by(Game.game_datetime)
        
        if max_games:
            games_query = games_query.limit(max_games)
        
        games = games_query.all()
        logger.info(f"Scraping detailed data for {len(games)} games from {season}")
        
        if not self.boxscore_scraper:
            self.boxscore_scraper = BoxscoreScraper(headless=True)
        
        successfully_scraped = 0
        failed_scrapes = 0
        skipped_existing = 0
        
        for i, game in enumerate(games, 1):
            try:
                logger.info(f"Processing game {i}/{len(games)}: {game.game_uid}")
                logger.info(f"  {game.away_team.name if game.away_team else 'Unknown'} @ {game.home_team.name if game.home_team else 'Unknown'}")
                
                # Check if already scraped
                boxscore_file = boxscores_dir / f"{game.game_uid}.json"
                if boxscore_file.exists():
                    logger.info("  ✅ Already exists - skipping")
                    skipped_existing += 1
                    continue
                
                # Scrape detailed data
                boxscore_data = self.boxscore_scraper.scrape_detailed_boxscore(game.game_uid)
                
                if boxscore_data:
                    # Save complete boxscore
                    with open(boxscore_file, 'w') as f:
                        json.dump(boxscore_data, f, indent=2)
                    
                    # Extract and save organized data
                    self._save_organized_game_data(game, boxscore_data, season_dir)
                    
                    successfully_scraped += 1
                    logger.info("  ✅ Successfully scraped")
                else:
                    failed_scrapes += 1
                    logger.warning("  ❌ Failed to scrape")
                
                # Be respectful to server
                time.sleep(3)
                
                # Progress updates
                if i % 10 == 0:
                    logger.info(f"Progress: {i}/{len(games)} processed")
                
            except Exception as e:
                logger.error(f"Error processing game {game.game_uid}: {e}")
                failed_scrapes += 1
                continue
        
        results = {
            "total_games": len(games),
            "successfully_scraped": successfully_scraped,
            "failed_scrapes": failed_scrapes,
            "skipped_existing": skipped_existing
        }
        
        logger.info(f"Detailed scraping complete for {season}:")
        logger.info(f"  Successfully scraped: {successfully_scraped}")
        logger.info(f"  Failed: {failed_scrapes}")
        logger.info(f"  Skipped (already existed): {skipped_existing}")
        
        return results
    
    def _save_organized_game_data(self, game: Game, boxscore_data: dict, season_dir: Path):
        """Save organized game data to separate files"""
        
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
            "away_score": game.away_score,
            "scraped_at": datetime.utcnow().isoformat()
        }
        
        # Save team stats
        team_stats = boxscore_data.get('team_stats', {})
        if team_stats:
            team_stats_data = {**game_info, "team_stats": team_stats}
            team_stats_file = season_dir / "team_stats" / f"{game.game_uid}_team_stats.json"
            with open(team_stats_file, 'w') as f:
                json.dump(team_stats_data, f, indent=2)
        
        # Save expected points if available
        expected_points = team_stats.get('expected_points', [])
        if expected_points:
            ep_data = {**game_info, "expected_points": expected_points}
            ep_file = season_dir / "expected_points" / f"{game.game_uid}_expected_points.json"
            with open(ep_file, 'w') as f:
                json.dump(ep_data, f, indent=2)
        
        # Save player stats
        player_stats = boxscore_data.get('player_stats', {})
        if player_stats:
            player_data = {**game_info, "player_stats": player_stats}
            player_file = season_dir / "player_stats" / f"{game.game_uid}_player_stats.json"
            with open(player_file, 'w') as f:
                json.dump(player_data, f, indent=2)
    
    def _create_season_summary(self, season: int, season_dir: Path, validation: dict, detailed_results: dict):
        """Create comprehensive season summary"""
        
        summary = {
            "season": season,
            "generated_at": datetime.utcnow().isoformat(),
            "validation": validation,
            "detailed_scraping": detailed_results,
            "data_files": {
                "schedule_csv": f"schedule_{season}.csv",
                "validation_report": "validation_report.json",
                "boxscores_directory": "boxscores/",
                "team_stats_directory": "team_stats/",
                "player_stats_directory": "player_stats/",
                "expected_points_directory": "expected_points/"
            }
        }
        
        # Count actual files created
        summary["file_counts"] = {
            "boxscores": len(list((season_dir / "boxscores").glob("*.json"))),
            "team_stats": len(list((season_dir / "team_stats").glob("*.json"))),
            "player_stats": len(list((season_dir / "player_stats").glob("*.json"))),
            "expected_points": len(list((season_dir / "expected_points").glob("*.json")))
        }
        
        # Save summary
        with open(season_dir / "season_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Create CSV summaries for easy viewing
        self._create_csv_summaries(season, season_dir)
    
    def _create_csv_summaries(self, season: int, season_dir: Path):
        """Create CSV summary files from JSON data"""
        
        # Team stats summary
        team_stats_files = list((season_dir / "team_stats").glob("*.json"))
        if team_stats_files:
            team_data = []
            
            for file in team_stats_files:
                with open(file) as f:
                    data = json.load(f)
                    
                base_row = {
                    "game_id": data.get("game_id"),
                    "date": data.get("date"),
                    "home_team": data.get("home_team"),
                    "away_team": data.get("away_team"),
                    "home_score": data.get("home_score"),
                    "away_score": data.get("away_score")
                }
                
                # Add expected points if available
                ep_data = data.get("team_stats", {}).get("expected_points", [])
                if len(ep_data) >= 2:
                    for i, team_ep in enumerate(ep_data):
                        team_name = team_ep.get("", "")
                        prefix = "home" if team_name == data.get("home_team") else "away"
                        
                        base_row.update({
                            f"{prefix}_expected_points_offense": team_ep.get("Offense"),
                            f"{prefix}_expected_points_defense": team_ep.get("Defense"),
                            f"{prefix}_expected_points_special_teams": team_ep.get("Special Teams")
                        })
                
                team_data.append(base_row)
            
            if team_data:
                df = pd.DataFrame(team_data)
                df.to_csv(season_dir / f"team_stats_summary_{season}.csv", index=False)
        
        # Games summary with metadata
        boxscore_files = list((season_dir / "boxscores").glob("*.json"))
        if boxscore_files:
            games_summary = []
            
            for file in boxscore_files:
                with open(file) as f:
                    data = json.load(f)
                    
                game_info = data.get("game_info", {})
                venue_info = game_info.get("venue", "")
                
                summary_row = {
                    "game_id": data.get("game_id"),
                    "venue_info": venue_info,
                    "has_team_stats": bool(data.get("team_stats")),
                    "has_player_stats": bool(data.get("player_stats")),
                    "scoring_plays_count": len(data.get("scoring_summary", [])),
                    "team_stats_sections": len(data.get("team_stats", {})),
                    "player_stats_sections": len(data.get("player_stats", {}))
                }
                
                games_summary.append(summary_row)
            
            if games_summary:
                df = pd.DataFrame(games_summary)
                df.to_csv(season_dir / f"detailed_games_summary_{season}.csv", index=False)


def main():
    """Main interactive function"""
    print("🏈 NFL Integrated Season Data Scraper")
    print("=====================================")
    
    try:
        with IntegratedSeasonScraper() as scraper:
            
            # Show current status
            seasons_info = scraper.get_available_seasons()
            print("\n📊 Current Data Status:")
            for season, info in seasons_info.items():
                print(f"  {season}: {info['total_games']} games in DB, {info['detailed_games']} detailed ({info['completion_rate']})")
            
            # Season selection
            print("\n🎯 Season Selection:")
            print("1. 2024 season (most recent)")
            print("2. 2023 season")
            print("3. 2022 season")
            print("4. All seasons (2022-2024)")
            print("5. Custom season validation only")
            
            choice = input("\nEnter your choice (1-5): ").strip()
            
            # Processing options
            print("\n⚙️  Processing Options:")
            max_games = input("Maximum games to process for detailed scraping (press Enter for all): ").strip()
            max_games = int(max_games) if max_games.isdigit() else None
            
            force_refresh = input("Force refresh existing data? (y/N): ").strip().lower() == 'y'
            
            # Execute based on choice
            if choice == "1":
                result = scraper.scrape_complete_season(2024, force_refresh, max_games)
                print(f"\n✅ Season 2024 complete! Data in: {result['data_directory']}")
                
            elif choice == "2":
                result = scraper.scrape_complete_season(2023, force_refresh, max_games)
                print(f"\n✅ Season 2023 complete! Data in: {result['data_directory']}")
                
            elif choice == "3":
                result = scraper.scrape_complete_season(2022, force_refresh, max_games)
                print(f"\n✅ Season 2022 complete! Data in: {result['data_directory']}")
                
            elif choice == "4":
                print("\n🔄 Processing all seasons...")
                for season in [2022, 2023, 2024]:
                    print(f"\n--- Processing {season} ---")
                    result = scraper.scrape_complete_season(season, force_refresh, max_games)
                    print(f"✅ Season {season} complete!")
                print(f"\n🎉 All seasons processed! Data in: {scraper.data_dir.absolute()}")
                
            elif choice == "5":
                season = input("Enter season to validate (2022-2024): ").strip()
                if season.isdigit() and int(season) in [2022, 2023, 2024]:
                    validation = scraper.validate_season_data(int(season))
                    print(f"\n📋 Validation Results for {season}:")
                    print(f"  Total games: {validation['total_games']}")
                    print(f"  Games with results: {validation['games_with_results']}")
                    print(f"  Games by type: {validation['games_by_type']}")
                    if validation['duplicate_game_ids']:
                        print(f"  ⚠️  Duplicates found: {len(validation['duplicate_game_ids'])}")
                else:
                    print("❌ Invalid season")
            else:
                print("❌ Invalid choice")
                
    except KeyboardInterrupt:
        print("\n\n⏹️  Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Error during integrated scraping: {e}")
        raise


if __name__ == "__main__":
    main()