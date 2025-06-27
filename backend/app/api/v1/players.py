from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ...core.database import get_db
from ...models import Player
from ...schemas.players import PlayerCreate, PlayerResponse, PlayerUpdate

router = APIRouter()


@router.get("/", response_model=List[PlayerResponse])
def get_players(
    team_uid: Optional[str] = Query(None, description="Filter by team"),
    position: Optional[str] = Query(None, description="Filter by position"),
    name: Optional[str] = Query(None, description="Filter by player name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    query = db.query(Player)
    
    if team_uid:
        query = query.filter(Player.team_uid == team_uid)
    if position:
        query = query.filter(Player.position.ilike(f"%{position}%"))
    if name:
        query = query.filter(Player.name.ilike(f"%{name}%"))
    
    players = query.offset(skip).limit(limit).all()
    return players


@router.get("/{player_uid}", response_model=PlayerResponse)
def get_player(player_uid: str, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.player_uid == player_uid).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player


@router.get("/team/{team_uid}", response_model=List[PlayerResponse])
def get_team_players(
    team_uid: str,
    position: Optional[str] = Query(None, description="Filter by position"),
    db: Session = Depends(get_db)
):
    """Get all players for a specific team"""
    query = db.query(Player).filter(Player.team_uid == team_uid)
    
    if position:
        query = query.filter(Player.position.ilike(f"%{position}%"))
    
    players = query.order_by(Player.jersey_number).all()
    return players


@router.get("/position/{position}", response_model=List[PlayerResponse])
def get_players_by_position(
    position: str,
    team_uid: Optional[str] = Query(None, description="Filter by team"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Get all players for a specific position"""
    query = db.query(Player).filter(Player.position.ilike(f"%{position}%"))
    
    if team_uid:
        query = query.filter(Player.team_uid == team_uid)
    
    players = query.limit(limit).all()
    return players