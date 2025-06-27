from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, ForeignKey, Index, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from ..core.database import Base


class League(enum.Enum):
    NFL = "NFL"
    CFL = "CFL"
    NCAA = "NCAA"


class Team(Base):
    __tablename__ = "teams"
    
    team_uid = Column(String, primary_key=True, index=True)
    league = Column(Enum(League), nullable=False)
    city = Column(String)
    name = Column(String, nullable=False)
    abbreviation = Column(String)
    stadium_name = Column(String)
    stadium_capacity = Column(Integer)
    latitude = Column(Float)
    longitude = Column(Float)
    founded_year = Column(Integer)
    conference = Column(String)
    division = Column(String)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source = Column(String)
    
    # Relationships
    home_games = relationship("Game", back_populates="home_team", foreign_keys="Game.home_team_uid")
    away_games = relationship("Game", back_populates="away_team", foreign_keys="Game.away_team_uid")
    players = relationship("Player", back_populates="team")


class Game(Base):
    __tablename__ = "games"
    
    game_uid = Column(String, primary_key=True, index=True)
    league = Column(Enum(League), nullable=False)
    season = Column(Integer, nullable=False)
    week = Column(Integer)
    game_type = Column(String)  # regular, playoff, championship
    
    home_team_uid = Column(String, ForeignKey("teams.team_uid"))
    away_team_uid = Column(String, ForeignKey("teams.team_uid"))
    
    game_datetime = Column(DateTime, nullable=True)  # Temporarily allow NULL while fixing parsing
    location = Column(String)
    venue = Column(String)
    
    home_score = Column(Integer)
    away_score = Column(Integer)
    overtime = Column(Integer, default=0)
    
    weather_temp = Column(Float)
    weather_condition = Column(String)
    weather_wind_speed = Column(Float)
    
    attendance = Column(Integer)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source = Column(String)
    raw_data = Column(JSON)
    
    # Relationships
    home_team = relationship("Team", back_populates="home_games", foreign_keys=[home_team_uid])
    away_team = relationship("Team", back_populates="away_games", foreign_keys=[away_team_uid])
    player_stats = relationship("PlayerStat", back_populates="game")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_game_date', 'game_datetime'),
        Index('idx_game_season_week', 'season', 'week'),
        Index('idx_game_teams', 'home_team_uid', 'away_team_uid'),
    )


class Player(Base):
    __tablename__ = "players"
    
    player_uid = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    position = Column(String)
    jersey_number = Column(Integer)
    birthdate = Column(DateTime)
    height_inches = Column(Integer)
    weight_lbs = Column(Integer)
    college = Column(String)
    draft_year = Column(Integer)
    draft_round = Column(Integer)
    draft_pick = Column(Integer)
    
    team_uid = Column(String, ForeignKey("teams.team_uid"))
    team_history = Column(JSON)  # Array of {team_uid, start_date, end_date}
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source = Column(String)
    
    # Relationships
    team = relationship("Team", back_populates="players")
    stats = relationship("PlayerStat", back_populates="player")


class PlayerStat(Base):
    __tablename__ = "player_stats"
    
    stat_uid = Column(String, primary_key=True, index=True)
    player_uid = Column(String, ForeignKey("players.player_uid"))
    game_uid = Column(String, ForeignKey("games.game_uid"))
    
    # Passing stats
    pass_attempts = Column(Integer, default=0)
    pass_completions = Column(Integer, default=0)
    pass_yards = Column(Integer, default=0)
    pass_touchdowns = Column(Integer, default=0)
    pass_interceptions = Column(Integer, default=0)
    pass_rating = Column(Float)
    
    # Rushing stats
    rush_attempts = Column(Integer, default=0)
    rush_yards = Column(Integer, default=0)
    rush_touchdowns = Column(Integer, default=0)
    rush_long = Column(Integer, default=0)
    
    # Receiving stats
    receptions = Column(Integer, default=0)
    receiving_yards = Column(Integer, default=0)
    receiving_touchdowns = Column(Integer, default=0)
    receiving_targets = Column(Integer, default=0)
    
    # Defensive stats
    tackles = Column(Integer, default=0)
    sacks = Column(Float, default=0)
    interceptions = Column(Integer, default=0)
    forced_fumbles = Column(Integer, default=0)
    fumble_recoveries = Column(Integer, default=0)
    
    # Special teams
    field_goals_made = Column(Integer, default=0)
    field_goals_attempted = Column(Integer, default=0)
    extra_points_made = Column(Integer, default=0)
    punts = Column(Integer, default=0)
    punt_yards = Column(Integer, default=0)
    
    # General
    fumbles = Column(Integer, default=0)
    fumbles_lost = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source = Column(String)
    
    # Relationships
    player = relationship("Player", back_populates="stats")
    game = relationship("Game", back_populates="player_stats")
    
    # Indexes
    __table_args__ = (
        Index('idx_player_game', 'player_uid', 'game_uid'),
        Index('idx_stat_game', 'game_uid'),
    )