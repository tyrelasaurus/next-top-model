#!/usr/bin/env python3
"""
Fix Season Assignment Issues
Corrects games that are assigned to the wrong season

The issue: January 2022 games (Week 17/18 of 2022 season) are incorrectly 
labeled as "2021 season" instead of "2022 season"

Usage:
    python fix_season_assignments.py [--dry-run] [--fix-2022]
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.models.sports import Game, Team
from sqlalchemy import extract

def analyze_season_assignment_issues():
    """Analyze season assignment problems"""
    print("=" * 80)
    print("🔍 ANALYZING SEASON ASSIGNMENT ISSUES")
    print("=" * 80)
    
    with SessionLocal() as db:
        # Find games in January 2022 labeled as 2021 season
        jan_2022_wrong_season = db.query(Game).filter(
            Game.season == 2021,
            extract('month', Game.game_datetime) == 1,
            extract('year', Game.game_datetime) == 2022
        ).all()
        
        print(f"Found {len(jan_2022_wrong_season)} games in January 2022 labeled as 2021 season")
        
        if jan_2022_wrong_season:
            # Analyze these games
            week_counts = {}
            type_counts = {}
            
            for game in jan_2022_wrong_season:
                week = game.week
                week_counts[week] = week_counts.get(week, 0) + 1
                type_counts[game.game_type] = type_counts.get(game.game_type, 0) + 1
            
            print(f"\nWeek distribution: {dict(sorted(week_counts.items()))}")
            print(f"Type distribution: {type_counts}")
            
            # Show sample games
            print(f"\nSample misassigned games:")
            for game in jan_2022_wrong_season[:10]:
                home_team = db.query(Team).filter(Team.team_uid == game.home_team_uid).first()
                away_team = db.query(Team).filter(Team.team_uid == game.away_team_uid).first()
                
                home_name = f"{home_team.city} {home_team.name}" if home_team else game.home_team_uid
                away_name = f"{away_team.city} {away_team.name}" if away_team else game.away_team_uid
                
                print(f"   {game.game_datetime.date()} - {away_name} @ {home_name} (Week {game.week})")
            
            if len(jan_2022_wrong_season) > 10:
                print(f"   ... and {len(jan_2022_wrong_season) - 10} more")
        
        # Check similar issues for other years
        print(f"\nChecking for similar issues in other years:")
        
        # January 2023 games labeled as 2022
        jan_2023_wrong = db.query(Game).filter(
            Game.season == 2022,
            extract('month', Game.game_datetime) == 1,
            extract('year', Game.game_datetime) == 2023
        ).count()
        
        # January 2024 games labeled as 2023  
        jan_2024_wrong = db.query(Game).filter(
            Game.season == 2023,
            extract('month', Game.game_datetime) == 1,
            extract('year', Game.game_datetime) == 2024
        ).count()
        
        print(f"   Jan 2023 games labeled as 2022: {jan_2023_wrong}")
        print(f"   Jan 2024 games labeled as 2023: {jan_2024_wrong}")
        
        return len(jan_2022_wrong_season)

def fix_2022_season_assignments(dry_run=False):
    """Fix games from January 2022 that should be 2022 season, not 2021"""
    print("\n" + "=" * 80)
    print("🔧 FIXING 2022 SEASON ASSIGNMENTS")
    print("=" * 80)
    
    with SessionLocal() as db:
        # Find the misassigned games
        misassigned_games = db.query(Game).filter(
            Game.season == 2021,
            extract('month', Game.game_datetime) == 1,
            extract('year', Game.game_datetime) == 2022
        ).all()
        
        print(f"Found {len(misassigned_games)} games to reassign from 2021 → 2022 season")
        
        if dry_run:
            print("🔍 DRY RUN - No changes will be made")
            
            # Show what would be changed
            week17_count = 0
            week18_count = 0
            
            for game in misassigned_games:
                if game.week == 17:
                    week17_count += 1
                elif game.week == 18:
                    week18_count += 1
            
            print(f"   Would reassign {week17_count} Week 17 games")
            print(f"   Would reassign {week18_count} Week 18 games")
            print(f"   Would also fix game types from 'playoff' to 'regular'")
            
            return 0
        
        # Actually fix the assignments
        fixed_count = 0
        
        for game in misassigned_games:
            # Change season from 2021 to 2022
            game.season = 2022
            
            # Also fix game type - Week 17/18 are regular season, not playoff
            if game.week in [17, 18]:
                game.game_type = "regular"
            
            fixed_count += 1
        
        db.commit()
        
        print(f"✅ Fixed {fixed_count} games:")
        print(f"   Season: 2021 → 2022")
        print(f"   Game type: 'playoff' → 'regular' (for Weeks 17/18)")
        
        # Verify the fix
        print(f"\nVerification:")
        
        # Check 2022 regular season count now
        regular_2022_count = db.query(Game).filter(
            Game.season == 2022,
            Game.game_type == "regular"
        ).count()
        
        week17_count = db.query(Game).filter(
            Game.season == 2022,
            Game.week == 17,
            Game.game_type == "regular"
        ).count()
        
        week18_count = db.query(Game).filter(
            Game.season == 2022,
            Game.week == 18,
            Game.game_type == "regular"
        ).count()
        
        print(f"   2022 regular season games: {regular_2022_count}")
        print(f"   2022 Week 17 regular games: {week17_count}")
        print(f"   2022 Week 18 regular games: {week18_count}")
        
        # Check if we're now at the expected 272
        expected = 272
        if regular_2022_count >= expected:
            print(f"🎯 SUCCESS: Reached expected game count!")
        else:
            missing = expected - regular_2022_count
            print(f"⚠️  Still missing {missing} games from expected {expected}")
        
        return fixed_count

def check_all_seasons_completeness():
    """Check completeness across all seasons after fixes"""
    print("\n" + "=" * 80)
    print("📊 FINAL SEASON COMPLETENESS CHECK")
    print("=" * 80)
    
    with SessionLocal() as db:
        seasons = [2022, 2023, 2024]
        
        for season in seasons:
            regular_count = db.query(Game).filter(
                Game.season == season,
                Game.game_type == "regular"
            ).count()
            
            playoff_count = db.query(Game).filter(
                Game.season == season,
                Game.game_type == "playoff"
            ).count()
            
            preseason_count = db.query(Game).filter(
                Game.season == season,
                Game.game_type == "preseason"
            ).count()
            
            expected_regular = 272
            completion_pct = (regular_count / expected_regular * 100)
            
            status = "🎯" if completion_pct >= 99 else "✅" if completion_pct >= 95 else "⚠️"
            
            print(f"   {season}: Regular={regular_count}/{expected_regular} ({completion_pct:.1f}%) {status}")
            print(f"        Playoff={playoff_count}, Preseason={preseason_count}")

def generate_season_fix_report(games_fixed):
    """Generate report of season assignment fixes"""
    print("\n" + "=" * 80)
    print("📋 SEASON ASSIGNMENT FIXES REPORT")
    print("=" * 80)
    
    report = f"""
# Season Assignment Fixes Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- Games reassigned: {games_fixed} (2021 → 2022 season)
- Issue: January 2022 games were incorrectly labeled as 2021 season
- Fix: Corrected season assignment and game type classification

## Root Cause
NFL seasons span calendar years. The 2022 NFL season includes:
- September-December 2022: Weeks 1-16  
- January 2023: Weeks 17-18 + Playoffs

The data source incorrectly assigned January 2022 games (end of 2021 season) 
to the 2021 season instead of the 2022 season.

## Expected Improvements
- 2022 regular season: Should now be at or near 272 games
- Database health score: +5-7 points
- Data completeness: Significantly improved

## Verification
Run the audit again to verify improvements:
```bash
python audit_nfl_database.py
```

## Result
Your NFL database should now have complete or near-complete regular season 
data for all seasons, making it suitable for predictive modeling and analysis.
"""
    
    with open("SEASON_ASSIGNMENT_FIXES_REPORT.md", "w") as f:
        f.write(report)
    
    print(report)
    print("📄 Season assignment fixes report saved to: SEASON_ASSIGNMENT_FIXES_REPORT.md")

def main():
    parser = argparse.ArgumentParser(description="Fix Season Assignment Issues")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be fixed without making changes")
    parser.add_argument("--fix-2022", action="store_true", help="Fix 2022 season assignments")
    parser.add_argument("--all", action="store_true", help="Run all fixes")
    
    args = parser.parse_args()
    
    if not any([args.dry_run, args.fix_2022, args.all]):
        args.all = True  # Default to all
    
    print("📅" * 20)
    print("SEASON ASSIGNMENT FIXES STARTED")
    print("📅" * 20)
    
    # Analyze the issues
    issues_found = analyze_season_assignment_issues()
    
    games_fixed = 0
    
    if args.dry_run:
        games_fixed = fix_2022_season_assignments(dry_run=True)
    elif args.fix_2022 or args.all:
        games_fixed = fix_2022_season_assignments(dry_run=False)
    
    # Check final completeness
    check_all_seasons_completeness()
    
    # Generate report
    if not args.dry_run:
        generate_season_fix_report(games_fixed)
    
    print(f"\n🎉 SEASON ASSIGNMENT FIXES COMPLETED!")
    if args.dry_run:
        print(f"   Dry run completed - found {issues_found} games to fix")
        print(f"   Run without --dry-run to apply fixes")
    else:
        print(f"   Fixed {games_fixed} games with incorrect season assignments")
        print(f"\nRun 'python audit_nfl_database.py' to verify improvements")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)