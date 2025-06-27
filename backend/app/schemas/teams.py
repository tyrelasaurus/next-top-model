from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from ..models import League


class TeamBase(BaseModel):
    team_uid: str
    league: League
    city: str
    name: str
    abbreviation: Optional[str] = None
    stadium_name: Optional[str] = None
    stadium_capacity: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    founded_year: Optional[int] = None
    conference: Optional[str] = None
    division: Optional[str] = None


class TeamCreate(TeamBase):
    source: str


class TeamUpdate(BaseModel):
    city: Optional[str] = None
    name: Optional[str] = None
    abbreviation: Optional[str] = None
    stadium_name: Optional[str] = None
    stadium_capacity: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    conference: Optional[str] = None
    division: Optional[str] = None


class TeamResponse(TeamBase):
    created_at: datetime
    updated_at: datetime
    source: str
    
    class Config:
        from_attributes = True