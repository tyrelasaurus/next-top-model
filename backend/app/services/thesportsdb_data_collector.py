#!/usr/bin/env python3
"""
TheSportsDB-First Data Collection Service for NFL Data
Uses TheSportsDB API as primary source for schedules/results
Only uses Pro Football Reference for detailed augmentation
"""

import logging
import asyncio
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..core.database import SessionLocal
from ..models.sports import Team, Game
from ..ingestion.thesportsdb import TheSportsDBClient
from ..scrapers.pro_football_reference_fixed import ProFootballReferenceScraper

logger = logging.getLogger(__name__)


class TheSportsDBDataCollector:
    """NFL data collection service using TheSportsDB as primary source"""
    
    def __init__(self):
        self.thesportsdb_client = None
        self.pff_scraper = None
        self.db: Session = None
        
    def __enter__(self):
        self.db = SessionLocal()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.thesportsdb_client:
            self.thesportsdb_client.close()
        if self.pff_scraper:
            self.pff_scraper.close()
        if self.db:
            self.db.close()
    
    def _setup_clients(self):
        """Initialize API client and scraper if not already done"""
        if not self.thesportsdb_client:
            self.thesportsdb_client = TheSportsDBClient()
        if not self.pff_scraper:
            self.pff_scraper = ProFootballReferenceScraper(headless=True)
    
    async def collect_complete_season_data(self, season: int, force_refresh: bool = False) -> Dict:
        """
        Collect complete season data using TheSportsDB first, then augment with PFR
        
        Args:
            season: NFL season year (e.g., 2022, 2023, 2024)
            force_refresh: If True, re-scrape even if data exists
            
        Returns:
            Dict with collection results and statistics
        """
        logger.info(f"Starting TheSportsDB-first data collection for {season} season")
        
        try:
            self._setup_clients()
            
            # Check existing data
            existing_games = self._get_existing_games(season)
            if existing_games and not force_refresh:
                logger.info(f"Found {len(existing_games)} existing games for {season}")
                return await self._verify_season_completeness(season)
            
            # Step 1: Collect schedule from TheSportsDB
            schedule_results = await self._collect_schedule_from_thesportsdb(season)
            
            # Step 2: Augment with detailed data from Pro Football Reference (selective)
            augmentation_results = await self._augment_with_pfr_data(season)
            
            # Verify data completeness
            verification_results = await self._verify_season_completeness(season)
            
            return {
                "season": season,
                "thesportsdb_schedule": schedule_results,
                "pfr_augmentation": augmentation_results,
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
    
    async def _collect_schedule_from_thesportsdb(self, season: int) -> Dict:
        """Collect schedule and results from TheSportsDB API"""
        logger.info(f"Collecting schedule from TheSportsDB for {season}")
        
        games_collected = []
        
        try:
            # NFL league ID in TheSportsDB is 4391
            nfl_league_id = "4391"
            
            # TheSportsDB uses season format like "2022-2023" for NFL
            season_format = f"{season}-{season + 1}"
            
            # Get schedule from TheSportsDB
            schedule_data = self.thesportsdb_client.get_schedule(nfl_league_id, season_format)
            
            logger.info(f"Retrieved {len(schedule_data)} events from TheSportsDB for {season}")
            
            for event in schedule_data:
                try:
                    # Create a simple mock league object with value attribute for compatibility
                    class MockLeague:
                        value = "NFL"
                    
                    game_data = self.thesportsdb_client.transform_game_data(event, MockLeague())
                    
                    # Map to our database format
                    mapped_data = self._map_thesportsdb_game_data(game_data, season)
                    
                    # Store in database
                    self._store_game(mapped_data)
                    
                    games_collected.append(game_data)
                    
                except Exception as e:
                    logger.error(f"Failed to process TheSportsDB event {event.get('idEvent', 'unknown')}: {e}")
                    continue
                
                # Rate limiting
                await asyncio.sleep(0.1)
            
            return {
                "source": "thesportsdb",
                "games_collected": len(games_collected),
                "games": games_collected
            }
            
        except Exception as e:
            logger.error(f"Failed to collect schedule from TheSportsDB: {e}")
            return {
                "source": "thesportsdb",
                "games_collected": 0,
                "games": [],
                "error": str(e)
            }
    
    async def _augment_with_pfr_data(self, season: int) -> Dict:
        """
        Gather detailed team statistics and match results from Pro Football Reference
        for regular season and playoff games only (skip preseason)
        """
        logger.info(f"Gathering detailed team stats and match results from PFR for {season}")
        
        augmented_games = []
        
        try:
            # Get only regular season and playoff games (skip preseason)
            all_games = self._get_existing_games(season)
            
            # Filter out preseason games (typically August games or games marked as preseason)
            games_to_augment = []
            for game in all_games:
                # Skip preseason games (August games or specific game types)
                if game.game_datetime and game.game_datetime.month == 8:
                    continue
                if game.game_type and 'pre' in game.game_type.lower():
                    continue
                games_to_augment.append(game)
            
            logger.info(f"Filtered {len(all_games)} total games to {len(games_to_augment)} regular/playoff games for PFR augmentation")
            
            # For now, skip PFR augmentation to speed up initial collection
            # This can be done in a separate batch process later
            logger.info("Skipping PFR augmentation for initial collection (can be done separately)")
            
            return {
                "source": "pro_football_reference",
                "games_augmented": 0,
                "augmented_game_ids": [],
                "note": "PFR augmentation skipped for speed - run separately if needed"
            }
            
        except Exception as e:
            logger.error(f"Failed to gather PFR team data: {e}")
            return {
                "source": "pro_football_reference",
                "games_augmented": 0,
                "augmented_game_ids": [],
                "error": str(e)
            }
    
    def _map_thesportsdb_game_data(self, thesportsdb_data: Dict, season: int) -> Dict:
        """Map TheSportsDB game data to our database format"""
        return {
            'game_uid': thesportsdb_data.get('game_uid'),
            'league': 'NFL',
            'season': season,
            'week': thesportsdb_data.get('week'),
            'game_type': self._determine_game_type(thesportsdb_data),
            'home_team_uid': thesportsdb_data.get('home_team_uid'),
            'away_team_uid': thesportsdb_data.get('away_team_uid'),
            'game_datetime': thesportsdb_data.get('game_datetime'),
            'venue': thesportsdb_data.get('venue'),
            'home_score': thesportsdb_data.get('home_score'),
            'away_score': thesportsdb_data.get('away_score'),
            'source': 'thesportsdb',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    
    def _determine_game_type(self, game_data: Dict) -> str:
        """Determine game type from TheSportsDB data"""
        # TheSportsDB might include round information
        week = game_data.get('week')
        
        if week and week > 18:
            return 'playoff'
        elif game_data.get('game_datetime'):
            # Check if it's in playoff months (January/February)
            game_date = game_data['game_datetime']
            if isinstance(game_date, datetime) and game_date.month in [1, 2]:
                return 'playoff'
        
        return 'regular'
    
    
    def _convert_to_pfr_game_id(self, game: Game) -> Optional[str]:
        """Convert our game UID to Pro Football Reference game ID format"""
        # This would need to be implemented based on PFR's ID format
        # For now, return None to skip PFR augmentation
        return None
    
    def _update_game_with_pfr_team_data(self, game: Game, pfr_data: Dict):
        """Update game with detailed team statistics and game data from Pro Football Reference"""
        # Focus on team-level statistics and game details (no player data)
        
        # Game environment data
        if pfr_data.get('attendance'):
            game.attendance = pfr_data['attendance']
        
        if pfr_data.get('weather_condition'):
            game.weather_condition = pfr_data['weather_condition']
            
        if pfr_data.get('weather_temp'):
            game.weather_temp = pfr_data['weather_temp']
            
        if pfr_data.get('weather_wind_speed'):
            game.weather_wind_speed = pfr_data['weather_wind_speed']
        
        # Venue information
        if pfr_data.get('venue'):
            game.venue = pfr_data['venue']
            
        if pfr_data.get('location'):
            game.location = pfr_data['location']
        
        # Game timing
        if pfr_data.get('overtime'):
            game.overtime = pfr_data['overtime']
        
        # Store detailed team statistics in raw_data field for now
        # Later we can expand the schema to include team-level stats
        if pfr_data.get('team_stats'):
            if not game.raw_data:
                game.raw_data = {}
            game.raw_data['pfr_team_stats'] = pfr_data['team_stats']
        
        game.updated_at = datetime.utcnow()
        self.db.commit()
    
    def _store_game(self, game_data: Dict):
        """Store game in the database"""
        try:
            # Check if game already exists
            existing_game = self.db.query(Game).filter(
                Game.game_uid == game_data.get('game_uid')
            ).first()
            
            if existing_game:
                # Update existing game
                for key, value in game_data.items():
                    if hasattr(existing_game, key) and value is not None:
                        setattr(existing_game, key, value)
                existing_game.updated_at = datetime.utcnow()
            else:
                # Create new game
                game = Game(**game_data)
                self.db.add(game)
            
            self.db.commit()
            logger.debug(f"Successfully stored game {game_data.get('game_uid')}")
            
        except Exception as e:
            logger.error(f"Failed to store game {game_data.get('game_uid', 'unknown')}: {e}")
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
        
        # Expected counts
        expected_regular = 272  # 17 weeks × 16 games
        expected_playoffs = 13  # 6 Wild Card + 4 Divisional + 2 Conference + 1 Super Bowl
        
        regular_count = game_types.get('regular', 0)
        playoff_count = sum(game_types.get(t, 0) for t in ['playoff', 'wildcard', 'divisional', 'conference', 'superbowl'])
        
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


class TheSportsDBDataCollectionManager:
    """High-level manager for TheSportsDB-first data collection operations"""
    
    @staticmethod
    async def collect_all_seasons(seasons: List[int] = [2022, 2023, 2024], force_refresh: bool = False) -> Dict:
        """Collect data for multiple seasons using TheSportsDB first"""
        results = {}
        
        for season in seasons:
            logger.info(f"Processing season {season} with TheSportsDB-first approach")
            
            with TheSportsDBDataCollector() as collector:
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
            with TheSportsDBDataCollector() as collector:
                completeness = await collector._verify_season_completeness(season)
                
                verification_results[season] = {
                    "completeness": completeness
                }
        
        return {
            "verification_results": verification_results,
            "timestamp": datetime.utcnow().isoformat()
        }