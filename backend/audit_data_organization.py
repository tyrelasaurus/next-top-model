#!/usr/bin/env python3
"""
Data Organization and Cleanliness Audit
Checks the overall structure, consistency, and organization of the NFL database
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.models.sports import Team, Game, TeamGameStat, TeamSeasonStat

def audit_data_organization():
    """Comprehensive audit of data organization and cleanliness"""
    
    print("🔍 NFL DATABASE ORGANIZATION AUDIT")
    print("=" * 60)
    
    with SessionLocal() as db:
        issues = []
        
        # 1. Team Data Consistency
        print("\n1. TEAM DATA ORGANIZATION:")
        teams = db.query(Team).all()
        
        thesportsdb_teams = sum(1 for t in teams if t.team_uid and t.team_uid.startswith('NFL_'))
        complete_teams = sum(1 for t in teams if all([
            t.team_uid, t.city, t.name, t.stadium_name, 
            t.latitude, t.longitude, t.conference, t.division
        ]))
        
        print(f"   Total teams: {len(teams)}")
        print(f"   TheSportsDB ID format: {thesportsdb_teams}/32")
        print(f"   Complete team records: {complete_teams}/32")
        
        if thesportsdb_teams != 32:
            issues.append("Inconsistent team ID format")
        if complete_teams < 30:
            issues.append("Incomplete team data")
        
        # 2. Game Data Organization
        print("\n2. GAME DATA ORGANIZATION:")
        
        seasons = db.query(Game.season).distinct().order_by(Game.season).all()
        game_types = db.query(Game.game_type).distinct().all()
        total_games = db.query(Game).count()
        games_with_dates = db.query(Game).filter(Game.game_datetime.isnot(None)).count()
        
        print(f"   Seasons: {[s[0] for s in seasons]}")
        print(f"   Game types: {sorted([gt[0] for gt in game_types if gt[0]])}")
        print(f"   Total games: {total_games}")
        print(f"   Games with dates: {games_with_dates}/{total_games}")
        
        if games_with_dates < total_games * 0.99:
            issues.append("Missing game dates")
        
        # Check for logical season structure
        for season in [s[0] for s in seasons if s[0] and s[0] >= 2022]:
            regular_count = db.query(Game).filter(
                Game.season == season,
                Game.game_type == "regular"
            ).count()
            
            print(f"   {season} regular season: {regular_count}/272 games")
            
            if regular_count < 260:  # Allow some variance
                issues.append(f"{season} season incomplete")
        
        # 3. Statistics Data Quality
        print("\n3. STATISTICS DATA ORGANIZATION:")
        
        total_team_stats = db.query(TeamGameStat).count()
        stats_with_yards = db.query(TeamGameStat).filter(TeamGameStat.total_yards.isnot(None)).count()
        stats_with_valid_teams = db.query(TeamGameStat).filter(
            TeamGameStat.team_uid.in_(db.query(Team.team_uid))
        ).count()
        
        print(f"   Team game statistics: {total_team_stats}")
        print(f"   Stats with total_yards: {stats_with_yards}/{total_team_stats}")
        print(f"   Stats with valid team refs: {stats_with_valid_teams}/{total_team_stats}")
        
        if stats_with_yards < total_team_stats * 0.95:
            issues.append("Missing statistics values")
        if stats_with_valid_teams < total_team_stats:
            issues.append("Broken foreign key relationships")
        
        # 4. ID System Consistency
        print("\n4. ID SYSTEM CONSISTENCY:")
        
        # Check game UID patterns
        sample_games = db.query(Game.game_uid).limit(100).all()
        uuid_pattern = sum(1 for g in sample_games if g[0] and '-' in g[0])
        
        print(f"   Game UIDs with UUID pattern: {uuid_pattern}/100 sampled")
        
        # Check team stat UIDs
        sample_stats = db.query(TeamGameStat.stat_uid).limit(100).all()
        stat_uuid_pattern = sum(1 for s in sample_stats if s[0] and '-' in s[0])
        
        print(f"   Stat UIDs with UUID pattern: {stat_uuid_pattern}/100 sampled")
        
        # 5. Data Relationships
        print("\n5. DATA RELATIONSHIP INTEGRITY:")
        
        # Check for orphaned records
        orphaned_stats = db.query(TeamGameStat).filter(
            ~TeamGameStat.game_uid.in_(db.query(Game.game_uid))
        ).count()
        
        games_missing_teams = db.query(Game).filter(
            ~Game.home_team_uid.in_(db.query(Team.team_uid))
        ).count()
        
        print(f"   Orphaned team statistics: {orphaned_stats}")
        print(f"   Games with invalid team refs: {games_missing_teams}")
        
        if orphaned_stats > 0:
            issues.append("Orphaned statistics records")
        if games_missing_teams > 0:
            issues.append("Games with invalid team references")
        
        # 6. Overall Assessment
        print("\n6. OVERALL DATA QUALITY ASSESSMENT:")
        
        if not issues:
            print("   ✅ Data is clean, uniform, and logically organized")
            print("   ✅ Consistent ID system using TheSportsDB")
            print("   ✅ Proper foreign key relationships")
            print("   ✅ Complete statistical coverage")
            return True
        else:
            print("   ⚠️  Issues found:")
            for issue in issues:
                print(f"      - {issue}")
            return False

if __name__ == "__main__":
    is_clean = audit_data_organization()
    sys.exit(0 if is_clean else 1)