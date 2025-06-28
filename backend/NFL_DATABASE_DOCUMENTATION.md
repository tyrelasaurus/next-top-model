# NFL Database Documentation

**Version**: 1.0  
**Last Updated**: 2025-06-28  
**Health Score**: 98/100  
**Status**: Production Ready

## Overview

This is a comprehensive NFL analytics database containing game results, team information, player data, and detailed statistics from the 2022-2024 seasons. The database is designed for advanced analytics, predictive modeling, and sports research.

## Database Architecture

### Primary Technology Stack
- **Database**: SQLite (nfl_data.db)
- **ORM**: SQLAlchemy
- **Primary Data Source**: TheSportsDB API
- **Enhanced Data Sources**: ESPN API
- **Language**: Python 3.x

### Core Design Principles
1. **TheSportsDB as Foundation**: All team IDs use TheSportsDB format as primary keys
2. **Data Source Mapping**: Other APIs (ESPN, etc.) are mapped to TheSportsDB IDs
3. **Comprehensive Coverage**: Focus on complete regular season and playoff data
4. **Statistical Depth**: Detailed team performance metrics for analysis

## Database Schema

### Core Tables

#### 1. Teams (`teams`)
**Purpose**: NFL team information and venue details

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `team_uid` | String (PK) | TheSportsDB team identifier | `NFL_134946` |
| `league` | String | Always "NFL" | `NFL` |
| `city` | String | Team city | `Arizona` |
| `name` | String | Team name | `Cardinals` |
| `abbreviation` | String | Standard NFL abbreviation | `ARI` |
| `stadium_name` | String | Home venue name | `State Farm Stadium` |
| `stadium_capacity` | Integer | Venue capacity | `63400` |
| `latitude` | Float | Stadium coordinates | `33.5276` |
| `longitude` | Float | Stadium coordinates | `-112.2626` |
| `conference` | String | NFC or AFC | `NFC` |
| `division` | String | Division name | `West` |
| `source` | String | Data source identifier | `NFL_DATABASE_BUILDER` |

#### 2. Games (`games`)
**Purpose**: Individual game information and results

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `game_uid` | String (PK) | Unique game identifier | `401547439` |
| `league` | String | Always "NFL" | `NFL` |
| `season` | Integer | NFL season year | `2023` |
| `week` | Float | Season week (1-18) | `17.0` |
| `game_type` | String | Game category | `regular` |
| `game_datetime` | DateTime | Game date and time | `2023-01-08 18:00:00` |
| `home_team_uid` | String (FK) | Home team reference | `NFL_134946` |
| `away_team_uid` | String (FK) | Away team reference | `NFL_134942` |
| `home_score` | Integer | Final home team score | `21` |
| `away_score` | Integer | Final away team score `14` |
| `attendance` | Integer | Game attendance | `65890` |
| `venue` | String | Stadium name | `State Farm Stadium` |
| `weather_temp` | Float | Game temperature (°F) | `72.0` |
| `weather_condition` | String | Weather description | `Dome` |
| `source` | String | Data source | `CSV_IMPORT` |

**Game Types**:
- `regular`: Regular season games (Weeks 1-18)
- `playoff`: Postseason games (Wildcard, Divisional, Conference, Super Bowl)
- `preseason`: Exhibition games (August)

#### 3. Team Game Statistics (`team_game_stats`)
**Purpose**: Detailed team performance metrics for individual games

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `stat_uid` | String (PK) | Unique statistic identifier | `401547439_NFL_134946` |
| `game_uid` | String (FK) | Game reference | `401547439` |
| `team_uid` | String (FK) | Team reference | `NFL_134946` |
| `is_home_team` | Integer | 1 if home, 0 if away | `1` |
| `total_yards` | Integer | Total offensive yards | `385` |
| `passing_yards` | Integer | Net passing yards | `234` |
| `rushing_yards` | Integer | Rushing yards | `151` |
| `first_downs` | Integer | First downs earned | `18` |
| `turnovers` | Integer | Total turnovers | `1` |
| `penalties` | Integer | Penalty count | `8` |
| `raw_box_score` | JSON | Complete ESPN statistics | `{...}` |
| `source` | String | Data source | `ESPN_API` |

#### 4. Team Season Statistics (`team_season_stats`)
**Purpose**: Aggregate team performance for entire seasons

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `season_stat_uid` | String (PK) | Unique identifier | `NFL_134946_2023` |
| `team_uid` | String (FK) | Team reference | `NFL_134946` |
| `season` | Integer | Season year | `2023` |
| `wins` | Integer | Regular season wins | `11` |
| `losses` | Integer | Regular season losses | `6` |
| `ties` | Integer | Regular season ties | `0` |
| `win_percentage` | Float | Win rate | `0.647` |
| `raw_season_data` | JSON | Complete ESPN data | `{...}` |

## Data Coverage and Quality

### Temporal Coverage
- **Primary Seasons**: 2022, 2023, 2024
- **Game Coverage**: 99.9% of regular season and playoff games
- **Historical Data**: Some 2021 season data available

### Data Completeness
| Category | Coverage | Games/Records |
|----------|----------|---------------|
| Regular Season Games | 99.9% | 815/816 games |
| Team Information | 100% | 32/32 teams |
| Game Statistics | 99.6-100% | ~1,912 records |
| Season Statistics | 100% | 96/96 records |
| Venue Data | 100% | All stadiums |
| Weather Data | 100% | All games |

### Missing Data
- **1 Game**: Buffalo Bills @ Cincinnati Bengals (2023-01-03) - Legitimately canceled due to medical emergency
- **No other significant gaps**

## ID System and Relationships

### TheSportsDB Team ID Mapping
The database uses TheSportsDB team IDs as primary keys. Here's the complete mapping:

| TheSportsDB ID | NFL Team | Abbreviation |
|----------------|----------|--------------|
| `NFL_134946` | Arizona Cardinals | ARI |
| `NFL_134942` | Atlanta Falcons | ATL |
| `NFL_134922` | Baltimore Ravens | BAL |
| `NFL_134918` | Buffalo Bills | BUF |
| `NFL_134943` | Carolina Panthers | CAR |
| `NFL_134938` | Chicago Bears | CHI |
| `NFL_134923` | Cincinnati Bengals | CIN |
| `NFL_134924` | Cleveland Browns | CLE |
| `NFL_134934` | Dallas Cowboys | DAL |
| `NFL_134930` | Denver Broncos | DEN |
| `NFL_134927` | Detroit Lions | DET |
| `NFL_134929` | Green Bay Packers | GB |
| `NFL_134932` | Houston Texans | HOU |
| `NFL_134926` | Indianapolis Colts | IND |
| `NFL_134948` | Jacksonville Jaguars | JAX |
| `NFL_134944` | Kansas City Chiefs | KC |
| `NFL_135908` | Las Vegas Raiders | LV |
| `NFL_134940` | Los Angeles Chargers | LAC |
| `NFL_134941` | Los Angeles Rams | LAR |
| `NFL_134920` | Miami Dolphins | MIA |
| `NFL_134939` | Minnesota Vikings | MIN |
| `NFL_134921` | New England Patriots | NE |
| `NFL_134925` | New Orleans Saints | NO |
| `NFL_134935` | New York Giants | NYG |
| `NFL_134936` | New York Jets | NYJ |
| `NFL_134931` | Philadelphia Eagles | PHI |
| `NFL_134937` | Pittsburgh Steelers | PIT |
| `NFL_135907` | San Francisco 49ers | SF |
| `NFL_134949` | Seattle Seahawks | SEA |
| `NFL_134928` | Tampa Bay Buccaneers | TB |
| `NFL_134945` | Tennessee Titans | TEN |
| `NFL_134919` | Washington Commanders | WAS |

### Foreign Key Relationships
```
Teams (1) ←→ (Many) Games [home_team_uid, away_team_uid]
Teams (1) ←→ (Many) TeamGameStats [team_uid]
Teams (1) ←→ (Many) TeamSeasonStats [team_uid]
Games (1) ←→ (Many) TeamGameStats [game_uid]
```

## Data Sources and Collection

### Primary Sources
1. **TheSportsDB**: Foundation data (teams, basic games)
2. **ESPN API**: Detailed statistics and box scores
3. **CSV Imports**: Historical game results
4. **Stadium Logic**: Venue and weather estimation

### Collection Scripts
- `build_nfl_database.py`: Comprehensive database builder
- `critical_games_collector.py`: Missing game statistics collector
- `team_id_mappings.py`: ID conversion utilities
- `audit_nfl_database.py`: Data quality monitoring

## NFL Season Structure Reference

### Regular Season (272 games total)
- **Teams**: 32 NFL teams
- **Games per team**: 17 regular season games
- **Weeks**: 18 weeks (Weeks 1-18)
- **Bye weeks**: Most weeks have 15 games (2 teams on bye)
- **Week 18**: Usually 16 games (all teams play)
- **Schedule**: September through January

### Playoff Structure (~14 games)
- **Wild Card**: 6 games
- **Divisional**: 4 games  
- **Conference Championships**: 2 games
- **Super Bowl**: 1 game
- **Schedule**: January through February

### Preseason (~64 games)
- **Exhibition games**: August
- **Variable schedule**: Not counted in regular analytics

## Usage Examples

### Basic Queries

```sql
-- Get all 2023 regular season games
SELECT * FROM games 
WHERE season = 2023 AND game_type = 'regular';

-- Get team statistics for a specific game
SELECT t.city, t.name, tgs.total_yards, tgs.passing_yards 
FROM team_game_stats tgs
JOIN teams t ON tgs.team_uid = t.team_uid
WHERE tgs.game_uid = '401547439';

-- Get season records for all teams in 2023
SELECT t.city, t.name, tss.wins, tss.losses, tss.win_percentage
FROM team_season_stats tss
JOIN teams t ON tss.team_uid = t.team_uid
WHERE tss.season = 2023
ORDER BY tss.win_percentage DESC;
```

### Python ORM Examples

```python
from app.core.database import SessionLocal
from app.models.sports import Team, Game, TeamGameStat

with SessionLocal() as db:
    # Get all teams
    teams = db.query(Team).all()
    
    # Get games for a specific team
    team = db.query(Team).filter(Team.team_uid == "NFL_134946").first()
    home_games = db.query(Game).filter(Game.home_team_uid == team.team_uid).all()
    
    # Get team statistics with relationships
    stats = db.query(TeamGameStat).join(Team).join(Game).filter(
        Game.season == 2023,
        Game.game_type == "regular"
    ).all()
```

## Data Validation and Monitoring

### Automated Checks
- **Health Score Monitoring**: `audit_nfl_database.py`
- **Data Completeness**: Coverage percentage tracking
- **Relationship Integrity**: Foreign key validation
- **Statistical Validity**: Range and logic checks

### Quality Metrics
- **Team Data**: 100% complete (32/32 teams)
- **Game Coverage**: 99.9% (815/816 games)
- **Statistics Coverage**: 99.6-100% by season
- **Data Integrity**: No orphaned records or broken relationships

## Maintenance and Updates

### Regular Maintenance
1. **Weekly**: Run audit script during season
2. **Monthly**: Check for new data sources
3. **Season End**: Complete data collection verification
4. **Off-season**: Historical data cleanup and optimization

### Update Procedures
1. **New Season Data**: Use `build_nfl_database.py`
2. **Missing Games**: Use `critical_games_collector.py`
3. **Data Issues**: Use appropriate fix scripts
4. **Validation**: Always run `audit_nfl_database.py` after changes

## File Organization

### Core Files
- `nfl_data.db`: Main database file
- `app/models/sports.py`: Database schema definitions
- `app/core/database.py`: Database connection and session management
- `team_id_mappings.py`: ID conversion utilities

### Scripts and Tools
- `build_nfl_database.py`: Complete database builder
- `audit_nfl_database.py`: Data quality monitoring
- `critical_games_collector.py`: Missing data collector
- `fix_*.py`: Various data correction utilities

### Documentation
- `NFL_DATABASE_DOCUMENTATION.md`: This document
- `NFL_DATABASE_AUDIT_REPORT.md`: Latest audit results
- Various fix and collection reports

## API Integration Notes

### TheSportsDB Integration
- **Base URL**: `https://www.thesportsdb.com/api/v1/json/`
- **Rate Limits**: Respectful usage (1-2 requests/second)
- **Data Format**: JSON responses
- **Team IDs**: Used as primary keys throughout system

### ESPN API Integration  
- **Base URL**: `https://site.api.espn.com/apis/site/v2/sports/football/nfl/`
- **Rate Limits**: 1.5-2 second delays between requests
- **Data Format**: Complex JSON with nested statistics
- **Usage**: Detailed game statistics and box scores

## Best Practices for Agents

### When Querying Data
1. **Always use TheSportsDB team IDs** for team references
2. **Filter by season and game_type** for specific analysis
3. **Join tables appropriately** for comprehensive data
4. **Check for NULL values** in optional fields

### When Adding New Data
1. **Maintain ID consistency** using TheSportsDB format
2. **Validate foreign key relationships** before inserting
3. **Use appropriate data sources** (TheSportsDB for teams, ESPN for stats)
4. **Run audit after major changes** to verify integrity

### When Building Analytics
1. **Exclude preseason games** for regular season analysis
2. **Account for the one missing game** (Buffalo-Cincinnati)
3. **Use complete seasons** (2022, 2024) for modeling when possible
4. **Consider bye weeks** when analyzing weekly performance

## Troubleshooting

### Common Issues
1. **Missing Statistics**: Use `critical_games_collector.py`
2. **Game Classification Errors**: Check `fix_game_categorization.py`
3. **ID Mapping Problems**: Reference `team_id_mappings.py`
4. **Data Quality Issues**: Run `audit_nfl_database.py`

### Getting Help
- Check audit reports for specific issues
- Review fix scripts for similar problems
- Verify data source APIs are accessible
- Ensure proper foreign key relationships

---

**This database represents a production-ready NFL analytics platform suitable for advanced statistical analysis, predictive modeling, and sports research. The 98/100 health score indicates excellent data quality and completeness.**