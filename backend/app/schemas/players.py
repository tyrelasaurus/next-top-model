from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


class TeamHistory(BaseModel):
    team_uid: str
    start_date: str
    end_date: Optional[str] = None


class PlayerBase(BaseModel):
    player_uid: str
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    position: Optional[str] = None
    jersey_number: Optional[int] = None
    birthdate: Optional[datetime] = None
    height_inches: Optional[int] = None
    weight_lbs: Optional[int] = None
    college: Optional[str] = None
    draft_year: Optional[int] = None
    draft_round: Optional[int] = None
    draft_pick: Optional[int] = None
    team_uid: Optional[str] = None
    team_history: Optional[List[Dict]] = None


class PlayerCreate(PlayerBase):
    source: str


class PlayerUpdate(BaseModel):
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    position: Optional[str] = None
    jersey_number: Optional[int] = None
    birthdate: Optional[datetime] = None
    height_inches: Optional[int] = None
    weight_lbs: Optional[int] = None
    college: Optional[str] = None
    draft_year: Optional[int] = None
    draft_round: Optional[int] = None
    draft_pick: Optional[int] = None
    team_uid: Optional[str] = None


class PlayerResponse(PlayerBase):
    created_at: datetime
    updated_at: datetime
    source: str
    
    class Config:
        from_attributes = True