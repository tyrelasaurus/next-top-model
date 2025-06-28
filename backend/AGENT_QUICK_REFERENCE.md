# NFL Database - Agent Quick Reference

**🎯 For AI agents working with this NFL database**

## Essential Facts

- **Health Score**: 98/100 (Production Ready)
- **Coverage**: 99.9% complete (815/816 games)
- **Primary ID System**: TheSportsDB format (`NFL_134946` = Arizona Cardinals)
- **Seasons**: 2022-2024 (complete), some 2021 data
- **Total Games**: 1,289 | Teams: 32 | Statistics: 1,912 records

## Quick Schema Reference

### Core Tables
```python
# Teams: 32 NFL teams with complete venue data
Team.team_uid        # Primary key: "NFL_134946" (TheSportsDB format)
Team.city           # "Arizona"  
Team.name           # "Cardinals"
Team.abbreviation   # "ARI"

# Games: Individual game results and info  
Game.game_uid       # Primary key: UUID or numeric
Game.season         # 2022, 2023, 2024
Game.game_type      # "regular", "playoff", "preseason" 
Game.week           # 1.0 to 18.0

# Team Game Stats: Detailed performance per game
TeamGameStat.total_yards    # Key metric for analysis
TeamGameStat.passing_yards  # Net passing
TeamGameStat.rushing_yards  # Rushing total
```

## ID System (Critical!)

**Always use TheSportsDB team IDs:**
```python
# Correct team references
"NFL_134946"  # Arizona Cardinals
"NFL_134944"  # Kansas City Chiefs  
"NFL_134918"  # Buffalo Bills

# Import mapping utilities
from team_id_mappings import get_nfl_abbr, get_thesportsdb_id
abbr = get_nfl_abbr("NFL_134946")  # Returns "ARI"
```

## NFL Structure Reference

```python
# Regular Season: 272 total games
# - 32 teams × 17 games ÷ 2 = 272 games
# - Weeks 1-18 (bye weeks = ~15 games/week)
# - September through January

# Playoff: ~14 games  
# - Wild Card (6) + Divisional (4) + Conference (2) + Super Bowl (1)

# Preseason: ~64 games (August, excluded from most analysis)
```

## Common Queries

### Get Team Statistics
```python
from app.core.database import SessionLocal
from app.models.sports import Team, Game, TeamGameStat

with SessionLocal() as db:
    # Team performance in 2023
    stats = db.query(TeamGameStat).join(Game).filter(
        Game.season == 2023,
        Game.game_type == "regular"
    ).all()
```

### Season Analysis
```python
# Regular season games only (exclude preseason)
regular_games = db.query(Game).filter(
    Game.season == 2023,
    Game.game_type == "regular"
).all()

# Team season records
from app.models.sports import TeamSeasonStat
records = db.query(TeamSeasonStat).filter(
    TeamSeasonStat.season == 2023
).all()
```

## Data Quality Notes

### ✅ What's Complete
- All 32 teams with full venue data
- 99.9% of regular season games (815/816)
- 100% team season statistics
- 100% venue and weather data
- Complete foreign key relationships

### ⚠️ What's Missing
- **1 game**: Buffalo @ Cincinnati (2023-01-03) - legitimately canceled
- **No other significant gaps**

## Best Practices for Agents

### DO ✅
```python
# Use TheSportsDB team IDs consistently
team_id = "NFL_134946"  # Arizona Cardinals

# Filter by game type for analysis
regular_season = Game.game_type == "regular"

# Join tables for comprehensive data
stats_with_teams = db.query(TeamGameStat).join(Team).all()

# Account for the one missing game in analysis
total_possible_games = 272  # Per season
actual_games = 271  # For 2023 (missing Buffalo-Cincinnati)
```

### DON'T ❌
```python
# Don't use NFL abbreviations as primary keys
team_id = "ARI"  # Wrong - use NFL_134946

# Don't include preseason in regular season analysis
all_games = Game.season == 2023  # Wrong - includes preseason

# Don't assume complete data without checking
# Always account for the one missing game
```

## Quick Validation

```python
# Verify data quality
def validate_season(season_year):
    with SessionLocal() as db:
        regular_count = db.query(Game).filter(
            Game.season == season_year,
            Game.game_type == "regular"
        ).count()
        
        expected = 272 if season_year != 2023 else 271
        return regular_count >= expected
```

## Key Files to Reference

- **Full Documentation**: `NFL_DATABASE_DOCUMENTATION.md`
- **Schema Definition**: `app/models/sports.py`
- **ID Mappings**: `team_id_mappings.py`
- **Quality Check**: `audit_nfl_database.py`

## Emergency Fixes

```bash
# If data seems wrong, run audit
python audit_nfl_database.py

# If missing games, try collector
python critical_games_collector.py

# If major issues, rebuild
python build_nfl_database.py
```

---
**Remember: This is a production-ready database (98/100 health score) suitable for serious analytics and predictive modeling. The data is clean, uniform, and logically organized with proper foreign key relationships.**