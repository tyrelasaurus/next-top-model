#!/usr/bin/env python3
"""
NFL Database Audit Tool
Comprehensive analysis of missing and inconsistent data in the NFL database

This script audits the database for:
- Missing game data
- Inconsistent team information
- Missing statistics
- Data quality issues
- Incomplete records

Usage:
    python audit_nfl_database.py [--detailed] [--seasons 2022,2023,2024]
"""

import argparse
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.models.sports import Team, Game, TeamGameStat, TeamSeasonStat
from sqlalchemy import extract, func, and_

def audit_teams():
    """Audit team data for completeness and consistency"""
    print("=" * 80)
    print("🏈 TEAM DATA AUDIT")
    print("=" * 80)
    
    issues = []
    
    with SessionLocal() as db:
        teams = db.query(Team).all()
        
        print(f"Total teams in database: {len(teams)}")
        
        # Check for missing essential data
        teams_missing_city = [t for t in teams if not t.city]
        teams_missing_name = [t for t in teams if not t.name]
        teams_missing_abbreviation = [t for t in teams if not t.abbreviation]
        teams_missing_stadium = [t for t in teams if not t.stadium_name]
        teams_missing_capacity = [t for t in teams if not t.stadium_capacity]
        teams_missing_coordinates = [t for t in teams if not t.latitude or not t.longitude]
        teams_missing_conference = [t for t in teams if not t.conference]
        teams_missing_division = [t for t in teams if not t.division]
        
        # Report issues
        if teams_missing_city:
            issues.append(f"Teams missing city: {[t.team_uid for t in teams_missing_city]}")
        
        if teams_missing_name:
            issues.append(f"Teams missing name: {[t.team_uid for t in teams_missing_name]}")
        
        if teams_missing_abbreviation:
            issues.append(f"Teams missing abbreviation: {[t.team_uid for t in teams_missing_abbreviation]}")
        
        if teams_missing_stadium:
            issues.append(f"Teams missing stadium: {[t.team_uid for t in teams_missing_stadium]}")
        
        if teams_missing_capacity:
            issues.append(f"Teams missing capacity: {[t.team_uid for t in teams_missing_capacity]}")
        
        if teams_missing_coordinates:
            issues.append(f"Teams missing coordinates: {[t.team_uid for t in teams_missing_coordinates]}")
        
        if teams_missing_conference:
            issues.append(f"Teams missing conference: {[t.team_uid for t in teams_missing_conference]}")
        
        if teams_missing_division:
            issues.append(f"Teams missing division: {[t.team_uid for t in teams_missing_division]}")
        
        # Check for expected number of teams (should be 32 NFL teams)
        expected_team_count = 32
        
        if len(teams) != expected_team_count:
            issues.append(f"Expected {expected_team_count} teams, found {len(teams)}")
        
        # Check for teams with TheSportsDB UIDs (this is correct - our primary system)
        thesportsdb_teams = [t for t in teams if t.team_uid.startswith("NFL_")]
        if len(thesportsdb_teams) != 32:
            issues.append(f"Not all teams using TheSportsDB UIDs: {len(thesportsdb_teams)}/32")
        else:
            print("✅ All teams correctly using TheSportsDB UIDs (our primary system)")
        
        # Summary
        if not issues:
            print("✅ Team data is complete and consistent")
        else:
            print("⚠️  Team data issues found:")
            for issue in issues:
                print(f"   • {issue}")
    
    return issues

def audit_games(seasons=None):
    """Audit game data for completeness and consistency"""
    print("\n" + "=" * 80)
    print("🏈 GAME DATA AUDIT")
    print("=" * 80)
    
    if seasons is None:
        seasons = [2022, 2023, 2024]
    
    issues = []
    
    with SessionLocal() as db:
        # Total games by season
        for season in seasons:
            total_games = db.query(Game).filter(Game.season == season).count()
            regular_games = db.query(Game).filter(
                Game.season == season,
                Game.game_type == "regular"
            ).count()
            playoff_games = db.query(Game).filter(
                Game.season == season,
                Game.game_type == "playoff"
            ).count()
            preseason_games = db.query(Game).filter(
                Game.season == season,
                extract('month', Game.game_datetime) == 8
            ).count()
            
            print(f"\n{season} Season:")
            print(f"   Total games: {total_games}")
            print(f"   Regular season: {regular_games}")
            print(f"   Playoff games: {playoff_games}")
            print(f"   Preseason games: {preseason_games}")
            
            # Expected: 272 regular season games (17 weeks × 32 teams ÷ 2)
            if regular_games < 270:  # Allow some flexibility
                issues.append(f"{season}: Only {regular_games} regular season games (expected ~272)")
        
        # Games with missing essential data
        games_missing_datetime = db.query(Game).filter(
            Game.season.in_(seasons),
            Game.game_datetime.is_(None)
        ).count()
        
        games_missing_teams = db.query(Game).filter(
            Game.season.in_(seasons),
            and_(Game.home_team_uid.is_(None), Game.away_team_uid.is_(None))
        ).count()
        
        games_missing_scores = db.query(Game).filter(
            Game.season.in_(seasons),
            Game.game_datetime.isnot(None),  # Completed games
            and_(Game.home_score.is_(None), Game.away_score.is_(None))
        ).count()
        
        games_missing_attendance = db.query(Game).filter(
            Game.season.in_(seasons),
            Game.attendance.is_(None)
        ).count()
        
        games_missing_venue = db.query(Game).filter(
            Game.season.in_(seasons),
            Game.venue.is_(None)
        ).count()
        
        games_missing_weather = db.query(Game).filter(
            Game.season.in_(seasons),
            Game.weather_temp.is_(None)
        ).count()
        
        # Report missing data
        if games_missing_datetime:
            issues.append(f"Games missing datetime: {games_missing_datetime}")
        
        if games_missing_teams:
            issues.append(f"Games missing team information: {games_missing_teams}")
        
        if games_missing_scores:
            issues.append(f"Completed games missing scores: {games_missing_scores}")
        
        if games_missing_attendance:
            issues.append(f"Games missing attendance: {games_missing_attendance}")
        
        if games_missing_venue:
            issues.append(f"Games missing venue: {games_missing_venue}")
        
        if games_missing_weather:
            issues.append(f"Games missing weather: {games_missing_weather}")
        
        # Check for impossible/inconsistent data
        games_with_negative_scores = db.query(Game).filter(
            Game.season.in_(seasons),
            and_(Game.home_score < 0, Game.away_score < 0)
        ).count()
        
        if games_with_negative_scores:
            issues.append(f"Games with negative scores: {games_with_negative_scores}")
        
        # Games in the future that have scores (suspicious)
        future_games_with_scores = db.query(Game).filter(
            Game.season.in_(seasons),
            Game.game_datetime > datetime.now(),
            and_(Game.home_score.isnot(None), Game.away_score.isnot(None))
        ).count()
        
        if future_games_with_scores:
            issues.append(f"Future games with scores (suspicious): {future_games_with_scores}")
        
        # Summary
        if not issues:
            print("\n✅ Game data is complete and consistent")
        else:
            print("\n⚠️  Game data issues found:")
            for issue in issues:
                print(f"   • {issue}")
    
    return issues

def audit_team_statistics(seasons=None):
    """Audit team game and season statistics"""
    print("\n" + "=" * 80)
    print("📊 TEAM STATISTICS AUDIT")
    print("=" * 80)
    
    if seasons is None:
        seasons = [2022, 2023, 2024]
    
    issues = []
    
    with SessionLocal() as db:
        # Game statistics coverage
        print("\nTEAM GAME STATISTICS:")
        
        for season in seasons:
            # Critical games (excluding preseason)
            critical_games = db.query(Game).filter(
                Game.season == season,
                Game.game_datetime.isnot(None),
                ~(extract('month', Game.game_datetime) == 8)  # Exclude August preseason
            ).count()
            
            # Games with statistics
            games_with_stats = db.query(Game).join(TeamGameStat).filter(
                Game.season == season,
                ~(extract('month', Game.game_datetime) == 8)
            ).distinct().count()
            
            # Team game stat records
            team_stat_records = db.query(TeamGameStat).join(Game).filter(
                Game.season == season
            ).count()
            
            coverage = (games_with_stats / critical_games * 100) if critical_games > 0 else 0
            
            print(f"   {season}: {games_with_stats}/{critical_games} games ({coverage:.1f}% coverage)")
            print(f"           {team_stat_records} team stat records")
            
            if coverage < 85:
                issues.append(f"{season}: Low game statistics coverage ({coverage:.1f}%)")
        
        # Season statistics coverage
        print("\nTEAM SEASON STATISTICS:")
        
        total_teams = db.query(Team).count()
        
        for season in seasons:
            season_stats = db.query(TeamSeasonStat).filter(
                TeamSeasonStat.season == season
            ).count()
            
            coverage = (season_stats / total_teams * 100) if total_teams > 0 else 0
            
            print(f"   {season}: {season_stats}/{total_teams} teams ({coverage:.1f}% coverage)")
            
            if coverage < 90:
                issues.append(f"{season}: Low season statistics coverage ({coverage:.1f}%)")
        
        # Check for inconsistent statistics
        invalid_stats = db.query(TeamGameStat).filter(
            and_(
                TeamGameStat.total_yards.isnot(None),
                TeamGameStat.total_yards < 0
            )
        ).count()
        
        if invalid_stats > 0:
            issues.append(f"Team game stats with negative total yards: {invalid_stats}")
        
        # Check for missing essential stats
        stats_missing_yards = db.query(TeamGameStat).filter(
            TeamGameStat.total_yards.is_(None)
        ).count()
        
        if stats_missing_yards > 0:
            issues.append(f"Team game stats missing total yards: {stats_missing_yards}")
        
        # Summary
        if not issues:
            print("\n✅ Team statistics are complete and consistent")
        else:
            print("\n⚠️  Team statistics issues found:")
            for issue in issues:
                print(f"   • {issue}")
    
    return issues

def analyze_missing_critical_games(seasons=None):
    """Analyze specific critical games that are missing statistics"""
    print("\n" + "=" * 80)
    print("🔍 MISSING CRITICAL GAMES ANALYSIS")
    print("=" * 80)
    
    if seasons is None:
        seasons = [2022, 2023, 2024]
    
    with SessionLocal() as db:
        # Find critical games without statistics
        missing_games = db.query(Game).filter(
            ~Game.game_uid.in_(
                db.query(TeamGameStat.game_uid).distinct()
            ),
            Game.season.in_(seasons),
            Game.game_datetime.isnot(None),
            ~(extract('month', Game.game_datetime) == 8)  # Exclude preseason
        ).order_by(Game.game_datetime).all()
        
        if not missing_games:
            print("✅ No critical games are missing statistics!")
            return []
        
        print(f"Found {len(missing_games)} critical games missing statistics:")
        print()
        
        # Group by season and type
        by_season = defaultdict(list)
        by_type = defaultdict(list)
        
        for game in missing_games:
            by_season[game.season].append(game)
            by_type[game.game_type].append(game)
        
        # Show breakdown
        print("BY SEASON:")
        for season in sorted(by_season.keys()):
            games = by_season[season]
            print(f"   {season}: {len(games)} games")
        
        print("\nBY TYPE:")
        for game_type in sorted(by_type.keys()):
            games = by_type[game_type]
            print(f"   {game_type}: {len(games)} games")
        
        print(f"\nSAMPLE MISSING GAMES:")
        for game in missing_games[:10]:
            with SessionLocal() as db:
                home_team = db.query(Team).filter(Team.team_uid == game.home_team_uid).first()
                away_team = db.query(Team).filter(Team.team_uid == game.away_team_uid).first()
                
                home_name = f"{home_team.city} {home_team.name}" if home_team else game.home_team_uid
                away_name = f"{away_team.city} {away_team.name}" if away_team else game.away_team_uid
                
                print(f"   {away_name} @ {home_name} ({game.game_datetime.date()}) - {game.game_type}")
        
        if len(missing_games) > 10:
            print(f"   ... and {len(missing_games) - 10} more")
        
        return missing_games

def audit_data_quality(seasons=None, detailed=False):
    """Check for data quality issues and anomalies"""
    print("\n" + "=" * 80)
    print("🔧 DATA QUALITY AUDIT")
    print("=" * 80)
    
    if seasons is None:
        seasons = [2022, 2023, 2024]
    
    issues = []
    
    with SessionLocal() as db:
        # Check for duplicate games
        duplicate_games = db.query(
            Game.home_team_uid,
            Game.away_team_uid,
            Game.game_datetime,
            func.count(Game.game_uid).label('count')
        ).filter(
            Game.season.in_(seasons)
        ).group_by(
            Game.home_team_uid,
            Game.away_team_uid,
            Game.game_datetime
        ).having(func.count(Game.game_uid) > 1).all()
        
        if duplicate_games:
            issues.append(f"Duplicate games found: {len(duplicate_games)} sets")
        
        # Check for games with same teams playing each other
        self_playing_games = db.query(Game).filter(
            Game.season.in_(seasons),
            Game.home_team_uid == Game.away_team_uid
        ).count()
        
        if self_playing_games:
            issues.append(f"Games where team plays itself: {self_playing_games}")
        
        # Check for unrealistic scores
        high_scoring_games = db.query(Game).filter(
            Game.season.in_(seasons),
            and_(
                Game.home_score.isnot(None),
                Game.away_score.isnot(None),
                (Game.home_score + Game.away_score) > 100
            )
        ).count()
        
        if high_scoring_games:
            issues.append(f"Games with combined score > 100: {high_scoring_games}")
        
        # Check for games with no score
        no_score_games = db.query(Game).filter(
            Game.season.in_(seasons),
            Game.game_datetime < datetime.now(),  # Past games
            and_(
                Game.home_score.is_(None),
                Game.away_score.is_(None)
            )
        ).count()
        
        if no_score_games:
            issues.append(f"Past games with no scores: {no_score_games}")
        
        # Check for unrealistic attendance
        high_attendance_games = db.query(Game).filter(
            Game.season.in_(seasons),
            Game.attendance > 150000  # No stadium has this capacity
        ).count()
        
        if high_attendance_games:
            issues.append(f"Games with unrealistic attendance (>150k): {high_attendance_games}")
        
        # Check for missing team references
        games_with_invalid_teams = db.query(Game).filter(
            Game.season.in_(seasons),
            and_(
                ~Game.home_team_uid.in_(db.query(Team.team_uid)),
                ~Game.away_team_uid.in_(db.query(Team.team_uid))
            )
        ).count()
        
        if games_with_invalid_teams:
            issues.append(f"Games referencing non-existent teams: {games_with_invalid_teams}")
        
        # Summary
        if not issues:
            print("✅ Data quality is good - no major issues found")
        else:
            print("⚠️  Data quality issues found:")
            for issue in issues:
                print(f"   • {issue}")
    
    return issues

def generate_audit_report(team_issues, game_issues, stats_issues, missing_games, quality_issues, seasons):
    """Generate comprehensive audit report with recommendations"""
    print("\n" + "=" * 80)
    print("📋 COMPREHENSIVE AUDIT REPORT")
    print("=" * 80)
    
    total_issues = len(team_issues) + len(game_issues) + len(stats_issues) + len(quality_issues)
    
    # Calculate overall health score
    health_score = max(0, 100 - (total_issues * 5) - (len(missing_games) * 2))
    
    report = f"""
# NFL Database Audit Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Seasons Audited: {', '.join(map(str, seasons))}

## 🏆 OVERALL HEALTH SCORE: {health_score}/100

## 📊 SUMMARY
- Team Data Issues: {len(team_issues)}
- Game Data Issues: {len(game_issues)}
- Statistics Issues: {len(stats_issues)}
- Data Quality Issues: {len(quality_issues)}
- Missing Critical Games: {len(missing_games)}

## 🔍 DETAILED FINDINGS

### Team Data Issues:
"""
    
    if team_issues:
        for issue in team_issues:
            report += f"- {issue}\n"
    else:
        report += "✅ No team data issues found\n"
    
    report += "\n### Game Data Issues:\n"
    if game_issues:
        for issue in game_issues:
            report += f"- {issue}\n"
    else:
        report += "✅ No game data issues found\n"
    
    report += "\n### Statistics Issues:\n"
    if stats_issues:
        for issue in stats_issues:
            report += f"- {issue}\n"
    else:
        report += "✅ No statistics issues found\n"
    
    report += "\n### Data Quality Issues:\n"
    if quality_issues:
        for issue in quality_issues:
            report += f"- {issue}\n"
    else:
        report += "✅ No data quality issues found\n"
    
    # Recommendations
    report += f"""

## 🎯 RECOMMENDATIONS

### Priority 1 (Critical):
"""
    
    if len(missing_games) > 50:
        report += "- Run critical games collector to gather missing statistics\n"
    
    if any("missing" in issue.lower() for issue in team_issues):
        report += "- Complete missing team information\n"
    
    if any("score" in issue.lower() for issue in game_issues):
        report += "- Update missing game scores\n"
    
    report += """
### Priority 2 (Important):
- Verify and correct any data quality issues
- Ensure all venue and attendance data is complete
- Add weather data for remaining games

### Priority 3 (Enhancement):
- Consider adding player-level statistics
- Implement data validation rules
- Set up automated data quality monitoring

## 🛠️ RECOMMENDED ACTIONS

1. **Run the comprehensive builder**:
   ```bash
   python build_nfl_database.py --seasons 2022,2023,2024
   ```

2. **Address missing critical games**:
   ```bash
   python critical_games_collector.py
   ```

3. **Monitor data quality regularly**:
   ```bash
   python audit_nfl_database.py --detailed
   ```

## 📈 DATABASE READINESS
"""
    
    if health_score >= 90:
        report += "🏆 EXCELLENT - Database is production-ready!\n"
    elif health_score >= 80:
        report += "✅ GOOD - Database is ready with minor improvements needed\n"
    elif health_score >= 70:
        report += "⚠️  FAIR - Some issues need attention before production use\n"
    else:
        report += "❌ POOR - Significant issues need resolution\n"
    
    # Save report
    with open("NFL_DATABASE_AUDIT_REPORT.md", "w") as f:
        f.write(report)
    
    print(report)
    print(f"\n📄 Detailed audit report saved to: NFL_DATABASE_AUDIT_REPORT.md")
    
    return health_score

def main():
    parser = argparse.ArgumentParser(description="NFL Database Audit Tool")
    parser.add_argument("--detailed", action="store_true", help="Include detailed analysis")
    parser.add_argument("--seasons", type=str, default="2022,2023,2024", 
                       help="Comma-separated list of seasons to audit")
    
    args = parser.parse_args()
    
    # Parse seasons
    seasons = [int(s.strip()) for s in args.seasons.split(",")]
    
    print("🔍" * 20)
    print("NFL DATABASE AUDIT STARTED")
    print("🔍" * 20)
    print(f"Auditing seasons: {seasons}")
    print(f"Detailed mode: {args.detailed}")
    print()
    
    # Run all audit checks
    team_issues = audit_teams()
    game_issues = audit_games(seasons)
    stats_issues = audit_team_statistics(seasons)
    missing_games = analyze_missing_critical_games(seasons)
    quality_issues = audit_data_quality(seasons, args.detailed)
    
    # Generate comprehensive report
    health_score = generate_audit_report(
        team_issues, game_issues, stats_issues, 
        missing_games, quality_issues, seasons
    )
    
    # Return appropriate exit code
    if health_score >= 80:
        print("\n🎉 AUDIT COMPLETED - Database is in good condition!")
        return 0
    else:
        print("\n⚠️  AUDIT COMPLETED - Issues found that need attention")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)