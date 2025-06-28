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
    league = Column(String, nullable=False, default="NFL")
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
    league = Column(String, nullable=False, default="NFL")  # Allow string for easier integration
    season = Column(Integer, nullable=False)
    week = Column(Float)  # Allow float for proper CSV compatibility
    game_type = Column(String, default="regular")  # regular, playoff, championship
    
    home_team_uid = Column(String, ForeignKey("teams.team_uid"), nullable=True)  # Allow NULL temporarily for easier integration
    away_team_uid = Column(String, ForeignKey("teams.team_uid"), nullable=True)  # Allow NULL temporarily for easier integration
    
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


class TeamGameStat(Base):
    """Team statistics for individual games"""
    __tablename__ = "team_game_stats"
    
    stat_uid = Column(String, primary_key=True, index=True)
    game_uid = Column(String, ForeignKey("games.game_uid"))
    team_uid = Column(String, ForeignKey("teams.team_uid"))
    is_home_team = Column(Integer, default=0)  # 1 if home, 0 if away
    
    # Offensive stats
    total_yards = Column(Integer)
    passing_yards = Column(Integer)
    rushing_yards = Column(Integer)
    first_downs = Column(Integer)
    third_down_attempts = Column(Integer)
    third_down_conversions = Column(Integer)
    fourth_down_attempts = Column(Integer)
    fourth_down_conversions = Column(Integer)
    red_zone_attempts = Column(Integer)
    red_zone_conversions = Column(Integer)
    time_of_possession_seconds = Column(Integer)
    
    # Turnovers
    turnovers = Column(Integer)
    fumbles = Column(Integer)
    fumbles_lost = Column(Integer)
    interceptions_thrown = Column(Integer)
    
    # Defensive stats
    sacks = Column(Float)
    tackles_for_loss = Column(Integer)
    interceptions = Column(Integer)
    fumbles_recovered = Column(Integer)
    forced_fumbles = Column(Integer)
    
    # Special teams
    field_goals_made = Column(Integer)
    field_goals_attempted = Column(Integer)
    extra_points_made = Column(Integer)
    extra_points_attempted = Column(Integer)
    punts = Column(Integer)
    punt_average = Column(Float)
    
    # Penalties
    penalties = Column(Integer)
    penalty_yards = Column(Integer)
    
    # Raw ESPN data
    raw_box_score = Column(JSON)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source = Column(String)
    
    # Relationships
    game = relationship("Game")
    team = relationship("Team")
    
    # Indexes
    __table_args__ = (
        Index('idx_team_game_stat', 'team_uid', 'game_uid'),
        Index('idx_game_team_stat', 'game_uid', 'team_uid'),
    )


class TeamSeasonStat(Base):
    """Team statistics for entire seasons"""
    __tablename__ = "team_season_stats"
    
    stat_uid = Column(String, primary_key=True, index=True)
    team_uid = Column(String, ForeignKey("teams.team_uid"))
    season = Column(Integer, nullable=False)
    season_type = Column(String, default="regular")  # regular, playoff
    
    # Record
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    ties = Column(Integer, default=0)
    win_percentage = Column(Float)
    
    # Scoring
    points_for = Column(Integer)
    points_against = Column(Integer)
    points_differential = Column(Integer)
    
    # Offensive stats (per game averages)
    total_yards_per_game = Column(Float)
    passing_yards_per_game = Column(Float)
    rushing_yards_per_game = Column(Float)
    first_downs_per_game = Column(Float)
    third_down_percentage = Column(Float)
    red_zone_percentage = Column(Float)
    
    # Defensive stats (per game averages)
    total_yards_allowed_per_game = Column(Float)
    passing_yards_allowed_per_game = Column(Float)
    rushing_yards_allowed_per_game = Column(Float)
    sacks_per_game = Column(Float)
    interceptions_per_game = Column(Float)
    
    # Turnover differential
    turnover_differential = Column(Integer)
    fumbles_lost_total = Column(Integer)
    interceptions_thrown_total = Column(Integer)
    fumbles_recovered_total = Column(Integer)
    interceptions_total = Column(Integer)
    
    # Rankings (1-32)
    offensive_rank = Column(Integer)
    defensive_rank = Column(Integer)
    scoring_offense_rank = Column(Integer)
    scoring_defense_rank = Column(Integer)
    
    # Division/Conference
    division_rank = Column(Integer)
    conference_rank = Column(Integer)
    playoff_seed = Column(Integer)
    
    # Raw ESPN data
    raw_season_data = Column(JSON)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source = Column(String)
    
    # Relationships
    team = relationship("Team")
    
    # Indexes
    __table_args__ = (
        Index('idx_team_season', 'team_uid', 'season'),
        Index('idx_season_stats', 'season', 'season_type'),
    )


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