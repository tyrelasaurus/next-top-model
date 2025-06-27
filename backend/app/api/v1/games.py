from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ...core.database import get_db
from ...models import Game, League, Team
from ...schemas.games import GameCreate, GameResponse, GameUpdate

router = APIRouter()


@router.get("/", response_model=List[GameResponse])
def get_games(
    league: Optional[League] = Query(None, description="Filter by league"),
    season: Optional[int] = Query(None, description="Filter by season"),
    week: Optional[int] = Query(None, description="Filter by week"),
    team_uid: Optional[str] = Query(None, description="Filter by team (home or away)"),
    date_from: Optional[str] = Query(None, description="Filter games from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter games to date (YYYY-MM-DD)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    query = db.query(Game)
    
    if league:
        query = query.filter(Game.league == league)
    if season:
        query = query.filter(Game.season == season)
    if week:
        query = query.filter(Game.week == week)
    if team_uid:
        query = query.filter((Game.home_team_uid == team_uid) | (Game.away_team_uid == team_uid))
    if date_from:
        try:
            date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(Game.game_datetime >= date_from_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_from format. Use YYYY-MM-DD")
    if date_to:
        try:
            date_to_dt = datetime.strptime(date_to, "%Y-%m-%d")
            query = query.filter(Game.game_datetime <= date_to_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_to format. Use YYYY-MM-DD")
    
    games = query.offset(skip).limit(limit).all()
    return games


@router.get("/{game_uid}", response_model=GameResponse)
def get_game(game_uid: str, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.game_uid == game_uid).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@router.get("/team/{team_uid}", response_model=List[GameResponse])
def get_team_games(
    team_uid: str, 
    season: Optional[int] = Query(None, description="Filter by season"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Get all games for a specific team"""
    query = db.query(Game).filter(
        (Game.home_team_uid == team_uid) | (Game.away_team_uid == team_uid)
    )
    
    if season:
        query = query.filter(Game.season == season)
    
    games = query.order_by(Game.game_datetime.desc()).limit(limit).all()
    return games


@router.get("/season/{season}", response_model=List[GameResponse])
def get_season_games(
    season: int,
    league: Optional[League] = Query(League.NFL, description="League filter"),
    week: Optional[int] = Query(None, description="Filter by week"),
    db: Session = Depends(get_db)
):
    """Get all games for a specific season"""
    query = db.query(Game).filter(Game.season == season)
    
    if league:
        query = query.filter(Game.league == league)
    if week:
        query = query.filter(Game.week == week)
    
    games = query.order_by(Game.week, Game.game_datetime).all()
    return games