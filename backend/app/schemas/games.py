from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from ..models import League


class GameBase(BaseModel):
    game_uid: str
    league: League
    season: int
    week: Optional[int] = None
    game_type: Optional[str] = None
    home_team_uid: str
    away_team_uid: str
    game_datetime: datetime
    location: Optional[str] = None
    venue: Optional[str] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    overtime: Optional[int] = 0
    weather_temp: Optional[float] = None
    weather_condition: Optional[str] = None
    weather_wind_speed: Optional[float] = None
    attendance: Optional[int] = None


class GameCreate(GameBase):
    source: str


class GameUpdate(BaseModel):
    season: Optional[int] = None
    week: Optional[int] = None
    game_type: Optional[str] = None
    game_datetime: Optional[datetime] = None
    location: Optional[str] = None
    venue: Optional[str] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    overtime: Optional[int] = None
    weather_temp: Optional[float] = None
    weather_condition: Optional[str] = None
    weather_wind_speed: Optional[float] = None
    attendance: Optional[int] = None


class GameResponse(GameBase):
    created_at: datetime
    updated_at: datetime
    source: str
    
    class Config:
        from_attributes = True