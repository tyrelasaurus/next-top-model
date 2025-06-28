#!/usr/bin/env python3
"""
Fix Week 17 Game Classification
Corrects 15 Week 17 games that are marked as 'playoff' instead of 'regular'

The issue: Week 17 games in January 2023 are marked as playoff when they 
should be regular season games.

Usage:
    python fix_week17_games.py [--dry-run]
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

def analyze_week17_issue():
    """Analyze the Week 17 classification issue"""
    print("=" * 80)
    print("🔍 ANALYZING WEEK 17 CLASSIFICATION ISSUE")
    print("=" * 80)
    
    with SessionLocal() as db:
        # Find Week 17 games marked as playoff
        week17_playoff_games = db.query(Game).filter(
            Game.season == 2022,
            Game.week == 17,
            Game.game_type == "playoff"
        ).all()
        
        print(f"Found {len(week17_playoff_games)} Week 17 games marked as 'playoff'")
        
        if week17_playoff_games:
            print(f"\nSample misclassified Week 17 games:")
            for game in week17_playoff_games[:5]:
                home_team = db.query(Team).filter(Team.team_uid == game.home_team_uid).first()
                away_team = db.query(Team).filter(Team.team_uid == game.away_team_uid).first()
                
                home_name = f"{home_team.city} {home_team.name}" if home_team else game.home_team_uid
                away_name = f"{away_team.city} {away_team.name}" if away_team else game.away_team_uid
                
                print(f"   {game.game_datetime.date()} - {away_name} @ {home_name}")
            
            if len(week17_playoff_games) > 5:
                print(f"   ... and {len(week17_playoff_games) - 5} more")
        
        # Check current Week 17 regular season count
        week17_regular = db.query(Game).filter(
            Game.season == 2022,
            Game.week == 17,
            Game.game_type == "regular"
        ).count()
        
        print(f"\nCurrent Week 17 breakdown:")
        print(f"   Regular season: {week17_regular}")
        print(f"   Playoff: {len(week17_playoff_games)}")
        print(f"   Total Week 17: {week17_regular + len(week17_playoff_games)}")
        
        return len(week17_playoff_games)

def fix_week17_classification(dry_run=False):
    """Fix Week 17 games that should be regular season"""
    print("\n" + "=" * 80)
    print("🔧 FIXING WEEK 17 GAME CLASSIFICATION")
    print("=" * 80)
    
    with SessionLocal() as db:
        # Find the misclassified Week 17 games
        week17_playoff_games = db.query(Game).filter(
            Game.season == 2022,
            Game.week == 17,
            Game.game_type == "playoff"
        ).all()
        
        print(f"Found {len(week17_playoff_games)} Week 17 games to fix")
        
        if dry_run:
            print("🔍 DRY RUN - No changes will be made")
            print(f"   Would change {len(week17_playoff_games)} games from 'playoff' to 'regular'")
            return 0
        
        # Actually fix the classifications
        fixed_count = 0
        
        for game in week17_playoff_games:
            game.game_type = "regular"
            fixed_count += 1
        
        db.commit()
        
        print(f"✅ Fixed {fixed_count} Week 17 games: 'playoff' → 'regular'")
        
        # Verify the fix
        print(f"\nVerification:")
        
        # Check 2022 regular season count now
        regular_2022_count = db.query(Game).filter(
            Game.season == 2022,
            Game.game_type == "regular"
        ).count()
        
        week17_regular_count = db.query(Game).filter(
            Game.season == 2022,
            Game.week == 17,
            Game.game_type == "regular"
        ).count()
        
        print(f"   2022 regular season games: {regular_2022_count}")
        print(f"   Week 17 regular games: {week17_regular_count}")
        
        # Check if we're now at the expected 272
        expected = 272
        if regular_2022_count >= expected:
            print(f"🎯 SUCCESS: Reached expected {expected} regular season games!")
        else:
            missing = expected - regular_2022_count
            print(f"⚠️  Still missing {missing} games from expected {expected}")
        
        return fixed_count

def verify_all_seasons():
    """Verify completeness across all seasons after fix"""
    print("\n" + "=" * 80)
    print("📊 FINAL COMPLETENESS VERIFICATION")
    print("=" * 80)
    
    with SessionLocal() as db:
        seasons = [2022, 2023, 2024]
        
        for season in seasons:
            regular_count = db.query(Game).filter(
                Game.season == season,
                Game.game_type == "regular"
            ).count()
            
            expected = 272
            completion_pct = (regular_count / expected * 100)
            
            status = "🎯" if completion_pct >= 99.5 else "✅" if completion_pct >= 95 else "⚠️"
            
            print(f"   {season}: {regular_count}/{expected} regular season games ({completion_pct:.1f}%) {status}")

def generate_week17_fix_report(games_fixed):
    """Generate report of Week 17 fixes"""
    print("\n" + "=" * 80)
    print("📋 WEEK 17 FIXES REPORT")
    print("=" * 80)
    
    report = f"""
# Week 17 Classification Fixes Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- Week 17 games fixed: {games_fixed}
- Issue: Week 17 games incorrectly marked as 'playoff' instead of 'regular'
- Impact: Resolves the missing 15 regular season games in 2022

## Root Cause
Week 17 is the final week of the NFL regular season, occurring in early January.
These games were incorrectly classified as playoff games instead of regular season games.

## Fix Applied
Changed game_type from 'playoff' to 'regular' for all Week 17 games in the 2022 season.

## Expected Results
- 2022 regular season should now have 272 games (complete)
- Database health score should improve to 95-100/100
- Data is now suitable for predictive modeling

## Verification
Run the audit again to verify the fix:
```bash
python audit_nfl_database.py
```

## Impact on Analysis
With complete regular season data, your database now supports:
- Accurate team performance analysis
- Reliable predictive modeling
- Complete season statistics
- Proper win/loss calculations
"""
    
    with open("WEEK17_FIXES_REPORT.md", "w") as f:
        f.write(report)
    
    print(report)
    print("📄 Week 17 fixes report saved to: WEEK17_FIXES_REPORT.md")

def main():
    parser = argparse.ArgumentParser(description="Fix Week 17 Game Classification")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be fixed without making changes")
    
    args = parser.parse_args()
    
    print("🏈" * 20)
    print("WEEK 17 CLASSIFICATION FIXES")
    print("🏈" * 20)
    
    # Analyze the issue
    issues_found = analyze_week17_issue()
    
    if issues_found == 0:
        print("\n✅ No Week 17 classification issues found!")
        return 0
    
    # Apply the fix
    if args.dry_run:
        games_fixed = fix_week17_classification(dry_run=True)
        print(f"\n🔍 Dry run completed - found {issues_found} games to fix")
        print(f"   Run without --dry-run to apply the fix")
    else:
        games_fixed = fix_week17_classification(dry_run=False)
        
        # Verify results
        verify_all_seasons()
        
        # Generate report
        generate_week17_fix_report(games_fixed)
        
        print(f"\n🎉 WEEK 17 FIXES COMPLETED!")
        print(f"   Fixed {games_fixed} games")
        print(f"\nRun 'python audit_nfl_database.py' to verify the improvement")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)