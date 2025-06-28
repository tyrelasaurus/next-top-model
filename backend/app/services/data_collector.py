#!/usr/bin/env python3
"""
Unified Data Collection Service for NFL Data
Integrates scraping, validation, and storage into core FastAPI application
"""

import logging
import asyncio
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..core.database import SessionLocal
from ..models.sports import Team, Game
from ..scrapers.pro_football_reference_fixed import ProFootballReferenceScraper

logger = logging.getLogger(__name__)


class NFLDataCollector:
    """Unified NFL data collection service"""
    
    def __init__(self):
        self.scraper = None
        self.db: Session = None
        
    def __enter__(self):
        self.db = SessionLocal()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.scraper:
            self.scraper.close()
        if self.db:
            self.db.close()
    
    def _setup_scraper(self):
        """Initialize the scraper if not already done"""
        if not self.scraper:
            self.scraper = ProFootballReferenceScraper(headless=True)
    
    async def collect_complete_season_data(self, season: int, force_refresh: bool = False) -> Dict:
        """
        Collect complete season data including all regular season and playoff games
        
        Args:
            season: NFL season year (e.g., 2022, 2023, 2024)
            force_refresh: If True, re-scrape even if data exists
            
        Returns:
            Dict with collection results and statistics
        """
        logger.info(f"Starting complete data collection for {season} season")
        
        try:
            self._setup_scraper()
            
            # Check existing data
            existing_games = self._get_existing_games(season)
            if existing_games and not force_refresh:
                logger.info(f"Found {len(existing_games)} existing games for {season}")
                return await self._verify_season_completeness(season)
            
            # Collect regular season games
            regular_season_results = await self._collect_regular_season(season)
            
            # Collect playoff games
            playoff_results = await self._collect_playoffs(season)
            
            # Verify data completeness
            verification_results = await self._verify_season_completeness(season)
            
            return {
                "season": season,
                "regular_season": regular_season_results,
                "playoffs": playoff_results,
                "verification": verification_results,
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to collect season data for {season}: {e}")
            return {
                "season": season,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _collect_regular_season(self, season: int) -> Dict:
        """Collect all regular season games for a given season"""
        logger.info(f"Collecting regular season games for {season}")
        
        games_collected = []
        weeks_processed = 0
        
        # NFL regular season is typically 18 weeks
        for week in range(1, 19):
            try:
                week_games = self.scraper.get_week_schedule(season, week)
                if week_games:
                    games_collected.extend(week_games)
                    weeks_processed += 1
                    
                    # Store games in database
                    self._store_games(week_games, season)
                    
                    logger.info(f"Week {week}: Collected {len(week_games)} games")
                    
                # Rate limiting
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Failed to collect week {week} for season {season}: {e}")
                continue
        
        return {
            "weeks_processed": weeks_processed,
            "games_collected": len(games_collected),
            "games": games_collected
        }
    
    async def _collect_playoffs(self, season: int) -> Dict:
        """Collect all playoff games for a given season"""
        logger.info(f"Collecting playoff games for {season}")
        
        playoff_rounds = [
            "Wild Card",
            "Divisional",
            "Conference Championships", 
            "Super Bowl"
        ]
        
        all_playoff_games = []
        
        for round_name in playoff_rounds:
            try:
                round_games = self.scraper.get_playoff_games(season, round_name)
                if round_games:
                    all_playoff_games.extend(round_games)
                    self._store_games(round_games, season)
                    logger.info(f"{round_name}: Collected {len(round_games)} games")
                
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Failed to collect {round_name} for season {season}: {e}")
                continue
        
        return {
            "rounds_processed": len(playoff_rounds),
            "playoff_games_collected": len(all_playoff_games),
            "games": all_playoff_games
        }
    
    def _store_games(self, games: List[Dict], season: int):
        """Store games in the database"""
        for game_data in games:
            try:
                # Check if game already exists
                existing_game = self.db.query(Game).filter(
                    Game.game_uid == game_data.get('game_id')
                ).first()
                
                if existing_game:
                    # Update existing game
                    for key, value in game_data.items():
                        if hasattr(existing_game, key):
                            setattr(existing_game, key, value)
                else:
                    # Create new game
                    game = Game(
                        game_uid=game_data.get('game_id'),
                        season=season,
                        week=game_data.get('week'),
                        game_type=game_data.get('game_type', 'regular'),
                        game_datetime=game_data.get('date'),
                        home_team_uid=game_data.get('home_team_uid'),
                        away_team_uid=game_data.get('away_team_uid'),
                        home_score=game_data.get('home_score'),
                        away_score=game_data.get('away_score')
                    )
                    self.db.add(game)
                
                self.db.commit()
                
            except Exception as e:
                logger.error(f"Failed to store game {game_data.get('game_id')}: {e}")
                self.db.rollback()
    
    def _get_existing_games(self, season: int) -> List[Game]:
        """Get existing games for a season from database"""
        return self.db.query(Game).filter(Game.season == season).all()
    
    async def _verify_season_completeness(self, season: int) -> Dict:
        """Verify that season data is complete"""
        games = self._get_existing_games(season)
        
        # Count games by type
        game_types = {}
        for game in games:
            game_type = game.game_type or 'regular'
            game_types[game_type] = game_types.get(game_type, 0) + 1
        
        # Expected counts (may vary by season)
        expected_regular = 272  # 17 weeks × 16 games
        expected_playoffs = 13  # 6 Wild Card + 4 Divisional + 2 Conference + 1 Super Bowl
        
        regular_count = game_types.get('regular', 0)
        playoff_count = sum(game_types.get(t, 0) for t in ['wildcard', 'divisional', 'conference', 'superbowl'])
        
        completeness = {
            "season": season,
            "total_games": len(games),
            "regular_season": {
                "count": regular_count,
                "expected": expected_regular,
                "complete": regular_count >= expected_regular
            },
            "playoffs": {
                "count": playoff_count,
                "expected": expected_playoffs,
                "complete": playoff_count >= expected_playoffs
            },
            "game_types": game_types,
            "missing_games": max(0, (expected_regular + expected_playoffs) - len(games))
        }
        
        return completeness
    
    async def collect_enhanced_game_data(self, game_id: str) -> Optional[Dict]:
        """Collect enhanced data for a specific game (boxscore, player stats)"""
        logger.info(f"Collecting enhanced data for game {game_id}")
        
        try:
            self._setup_scraper()
            
            # Get boxscore data
            boxscore = self.scraper.get_game_boxscore(game_id)
            
            # Get player stats
            player_stats = self.scraper.get_game_player_stats(game_id)
            
            return {
                "game_id": game_id,
                "boxscore": boxscore,
                "player_stats": player_stats,
                "collected_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to collect enhanced data for {game_id}: {e}")
            return None
    
    async def verify_data_consistency(self, season: int) -> Dict:
        """Verify data consistency for a season"""
        logger.info(f"Verifying data consistency for {season}")
        
        games = self._get_existing_games(season)
        
        issues = []
        
        for game in games:
            # Check for missing teams
            if not game.home_team_uid or not game.away_team_uid:
                issues.append(f"Game {game.game_uid}: Missing team assignments")
            
            # Check for invalid scores
            if game.home_score is not None and game.away_score is not None:
                if game.home_score < 0 or game.away_score < 0:
                    issues.append(f"Game {game.game_uid}: Invalid scores")
            
            # Check for missing dates
            if not game.game_datetime:
                issues.append(f"Game {game.game_uid}: Missing game date")
        
        return {
            "season": season,
            "games_checked": len(games),
            "issues_found": len(issues),
            "issues": issues,
            "data_quality": "good" if len(issues) == 0 else "needs_attention"
        }


class DataCollectionManager:
    """High-level manager for data collection operations"""
    
    @staticmethod
    async def collect_all_seasons(seasons: List[int] = [2022, 2023, 2024], force_refresh: bool = False) -> Dict:
        """Collect data for multiple seasons"""
        results = {}
        
        for season in seasons:
            logger.info(f"Processing season {season}")
            
            with NFLDataCollector() as collector:
                season_result = await collector.collect_complete_season_data(season, force_refresh)
                results[season] = season_result
        
        return {
            "seasons_processed": seasons,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    async def verify_all_data() -> Dict:
        """Verify data completeness and consistency across all seasons"""
        verification_results = {}
        
        for season in [2022, 2023, 2024]:
            with NFLDataCollector() as collector:
                completeness = await collector._verify_season_completeness(season)
                consistency = await collector.verify_data_consistency(season)
                
                verification_results[season] = {
                    "completeness": completeness,
                    "consistency": consistency
                }
        
        return {
            "verification_results": verification_results,
            "timestamp": datetime.utcnow().isoformat()
        }