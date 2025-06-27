from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ...core.database import get_db
from ...models import Team, League
from ...schemas.teams import TeamCreate, TeamResponse, TeamUpdate

router = APIRouter()


@router.get("/", response_model=List[TeamResponse])
def get_teams(
    league: Optional[League] = Query(None, description="Filter by league"),
    city: Optional[str] = Query(None, description="Filter by city"),
    name: Optional[str] = Query(None, description="Filter by team name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    query = db.query(Team)
    
    if league:
        query = query.filter(Team.league == league)
    if city:
        query = query.filter(Team.city.ilike(f"%{city}%"))
    if name:
        query = query.filter(Team.name.ilike(f"%{name}%"))
    
    teams = query.offset(skip).limit(limit).all()
    return teams


@router.get("/{team_uid}", response_model=TeamResponse)
def get_team(team_uid: str, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.team_uid == team_uid).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.post("/", response_model=TeamResponse, status_code=201)
def create_team(team: TeamCreate, db: Session = Depends(get_db)):
    db_team = Team(**team.dict())
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team


@router.put("/{team_uid}", response_model=TeamResponse)
def update_team(team_uid: str, team: TeamUpdate, db: Session = Depends(get_db)):
    db_team = db.query(Team).filter(Team.team_uid == team_uid).first()
    if not db_team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    for field, value in team.dict(exclude_unset=True).items():
        setattr(db_team, field, value)
    
    db.commit()
    db.refresh(db_team)
    return db_team