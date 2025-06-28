#!/usr/bin/env python3
"""
Data Management API Endpoints
Provides endpoints for data collection, verification, and management
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import logging

from ...core.database import get_db
from ...services.data_collector import NFLDataCollector, DataCollectionManager
from ...schemas.games import GameResponse
from ...models.sports import Game

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/collect/season/{season}")
async def collect_season_data(
    season: int,
    force_refresh: bool = False,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Collect complete data for a specific NFL season
    
    Args:
        season: NFL season year (2022, 2023, 2024)
        force_refresh: Whether to re-scrape existing data
        
    Returns:
        Collection results and statistics
    """
    if season < 2020 or season > 2024:
        raise HTTPException(status_code=400, detail="Season must be between 2020 and 2024")
    
    logger.info(f"Starting data collection for {season} season")
    
    try:
        with NFLDataCollector() as collector:
            results = await collector.collect_complete_season_data(season, force_refresh)
            
        return {
            "status": "success",
            "season": season,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Failed to collect season {season} data: {e}")
        raise HTTPException(status_code=500, detail=f"Data collection failed: {str(e)}")


@router.post("/collect/all-seasons")
async def collect_all_seasons_data(
    seasons: Optional[List[int]] = None,
    force_refresh: bool = False,
    background_tasks: BackgroundTasks = None
) -> Dict:
    """
    Collect data for multiple seasons (default: 2022, 2023, 2024)
    """
    if seasons is None:
        seasons = [2022, 2023, 2024]
    
    # Validate seasons
    for season in seasons:
        if season < 2020 or season > 2024:
            raise HTTPException(status_code=400, detail=f"Invalid season: {season}")
    
    logger.info(f"Starting data collection for seasons: {seasons}")
    
    try:
        results = await DataCollectionManager.collect_all_seasons(seasons, force_refresh)
        
        return {
            "status": "success",
            "seasons": seasons,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Failed to collect multi-season data: {e}")
        raise HTTPException(status_code=500, detail=f"Multi-season collection failed: {str(e)}")


@router.get("/verify/season/{season}")
async def verify_season_data(season: int, db: Session = Depends(get_db)) -> Dict:
    """
    Verify completeness and consistency of data for a specific season
    """
    if season < 2020 or season > 2024:
        raise HTTPException(status_code=400, detail="Season must be between 2020 and 2024")
    
    try:
        with NFLDataCollector() as collector:
            completeness = await collector._verify_season_completeness(season)
            consistency = await collector.verify_data_consistency(season)
            
        return {
            "season": season,
            "completeness": completeness,
            "consistency": consistency,
            "status": "verified"
        }
        
    except Exception as e:
        logger.error(f"Failed to verify season {season}: {e}")
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@router.get("/verify/all")
async def verify_all_data() -> Dict:
    """
    Verify completeness and consistency of all collected data
    """
    try:
        results = await DataCollectionManager.verify_all_data()
        
        return {
            "status": "verified",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Failed to verify all data: {e}")
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@router.get("/status/overview")
async def get_data_status_overview(db: Session = Depends(get_db)) -> Dict:
    """
    Get overview of current data status across all seasons
    """
    try:
        overview = {}
        
        for season in [2022, 2023, 2024]:
            games = db.query(Game).filter(Game.season == season).all()
            
            game_types = {}
            for game in games:
                game_type = game.game_type or 'regular'
                game_types[game_type] = game_types.get(game_type, 0) + 1
            
            overview[season] = {
                "total_games": len(games),
                "game_types": game_types,
                "last_game_date": max([g.game_datetime for g in games if g.game_datetime]) if games else None
            }
        
        return {
            "status": "success",
            "overview": overview,
            "total_games": sum(data["total_games"] for data in overview.values())
        }
        
    except Exception as e:
        logger.error(f"Failed to get data overview: {e}")
        raise HTTPException(status_code=500, detail=f"Overview generation failed: {str(e)}")


@router.post("/enhance/game/{game_id}")
async def collect_enhanced_game_data(game_id: str) -> Dict:
    """
    Collect enhanced data (boxscore, player stats) for a specific game
    """
    try:
        with NFLDataCollector() as collector:
            enhanced_data = await collector.collect_enhanced_game_data(game_id)
            
        if enhanced_data:
            return {
                "status": "success",
                "game_id": game_id,
                "data": enhanced_data
            }
        else:
            raise HTTPException(status_code=404, detail=f"Could not collect enhanced data for game {game_id}")
            
    except Exception as e:
        logger.error(f"Failed to collect enhanced data for {game_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Enhanced data collection failed: {str(e)}")


@router.get("/missing-games/{season}")
async def identify_missing_games(season: int, db: Session = Depends(get_db)) -> Dict:
    """
    Identify potentially missing games for a season
    """
    if season < 2020 or season > 2024:
        raise HTTPException(status_code=400, detail="Season must be between 2020 and 2024")
    
    try:
        games = db.query(Game).filter(Game.season == season).all()
        
        # Expected game structure
        expected_regular = 272  # 17 weeks × 16 games
        expected_playoffs = 13  # Wild Card (6) + Divisional (4) + Conference (2) + Super Bowl (1)
        
        regular_games = [g for g in games if (g.game_type or 'regular') == 'regular']
        playoff_games = [g for g in games if (g.game_type or 'regular') in ['wildcard', 'divisional', 'conference', 'superbowl']]
        
        # Analyze missing weeks
        weeks_with_games = set(g.week for g in regular_games if g.week)
        expected_weeks = set(range(1, 19))  # Weeks 1-18
        missing_weeks = expected_weeks - weeks_with_games
        
        missing_info = {
            "season": season,
            "regular_season": {
                "found": len(regular_games),
                "expected": expected_regular,
                "missing_count": max(0, expected_regular - len(regular_games)),
                "missing_weeks": sorted(list(missing_weeks))
            },
            "playoffs": {
                "found": len(playoff_games),
                "expected": expected_playoffs,
                "missing_count": max(0, expected_playoffs - len(playoff_games))
            },
            "total_missing": max(0, (expected_regular + expected_playoffs) - len(games))
        }
        
        return missing_info
        
    except Exception as e:
        logger.error(f"Failed to identify missing games for {season}: {e}")
        raise HTTPException(status_code=500, detail=f"Missing games analysis failed: {str(e)}")


@router.delete("/season/{season}")
async def delete_season_data(season: int, db: Session = Depends(get_db)) -> Dict:
    """
    Delete all data for a specific season (use with caution)
    """
    if season < 2020 or season > 2024:
        raise HTTPException(status_code=400, detail="Season must be between 2020 and 2024")
    
    try:
        deleted_count = db.query(Game).filter(Game.season == season).delete()
        db.commit()
        
        logger.info(f"Deleted {deleted_count} games from {season} season")
        
        return {
            "status": "success",
            "season": season,
            "deleted_games": deleted_count
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete season {season} data: {e}")
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")