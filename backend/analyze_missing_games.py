#!/usr/bin/env python3
"""
Analyze Missing Games - Categorize the 224 missing games
Identifies preseason vs legitimate regular season/playoff games
"""

import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.models.sports import Game, TeamGameStat, Team

def analyze_missing_games():
    """Comprehensive analysis of the 224 games without statistics"""
    
    with SessionLocal() as db:
        # Get games without stats
        games_without_stats = db.query(Game).filter(
            ~Game.game_uid.in_(
                db.query(TeamGameStat.game_uid).distinct()
            ),
            Game.season >= 2022,
            Game.game_datetime.isnot(None)
        ).order_by(Game.game_datetime).all()
        
        print(f"📊 ANALYSIS OF {len(games_without_stats)} MISSING GAMES")
        print("=" * 60)
        
        # Categorize games
        preseason_games = []  # August games
        early_season = []     # September regular season
        regular_season = []   # Oct-Dec regular season
        playoff_games = []    # January playoff games
        
        for game in games_without_stats:
            month = game.game_datetime.month
            
            if month == 8:  # August = preseason
                preseason_games.append(game)
            elif month == 9 and game.game_type == "regular":
                early_season.append(game)
            elif month in [10, 11, 12] and game.game_type == "regular":
                regular_season.append(game)
            elif month == 1 and game.game_type == "playoff":
                playoff_games.append(game)
            else:
                # Other cases
                if game.game_type == "regular":
                    regular_season.append(game)
                else:
                    playoff_games.append(game)
        
        print(f"🏈 PRESEASON GAMES (August): {len(preseason_games)}")
        print(f"🏈 EARLY REGULAR SEASON (September): {len(early_season)}")
        print(f"🏈 REGULAR SEASON (Oct-Dec): {len(regular_season)}")
        print(f"🏆 PLAYOFF GAMES (January): {len(playoff_games)}")
        print()
        
        # Show preseason sample
        print("PRESEASON GAMES (should not have detailed stats):")
        for game in preseason_games[:5]:
            home_team = db.query(Team).filter(Team.team_uid == game.home_team_uid).first()
            away_team = db.query(Team).filter(Team.team_uid == game.away_team_uid).first()
            print(f"  {away_team.city} {away_team.name} @ {home_team.city} {home_team.name} ({game.game_datetime.date()})")
        if len(preseason_games) > 5:
            print(f"  ... and {len(preseason_games) - 5} more preseason games")
        print()
        
        # Show critical missing games
        critical_games = regular_season + playoff_games
        print(f"🚨 CRITICAL MISSING GAMES: {len(critical_games)} (need statistics)")
        
        # Show some examples
        print("\nSample critical missing games:")
        for game in critical_games[:10]:
            home_team = db.query(Team).filter(Team.team_uid == game.home_team_uid).first()
            away_team = db.query(Team).filter(Team.team_uid == game.away_team_uid).first()
            print(f"  {away_team.city} {away_team.name} @ {home_team.city} {home_team.name} ({game.game_datetime.date()}) - {game.game_type}")
        
        if len(critical_games) > 10:
            print(f"  ... and {len(critical_games) - 10} more critical games")
        
        # Calculate real coverage
        total_games_with_season = db.query(Game).filter(Game.season >= 2022).count()
        legitimate_games = total_games_with_season - len(preseason_games)
        games_with_stats = db.query(Game).join(TeamGameStat).filter(Game.season >= 2022).distinct().count()
        
        real_coverage = (games_with_stats / legitimate_games * 100) if legitimate_games > 0 else 0
        
        print()
        print("📈 CORRECTED COVERAGE CALCULATION:")
        print(f"Total games in database: {total_games_with_season}")
        print(f"Preseason games (no stats needed): {len(preseason_games)}")
        print(f"Legitimate games needing stats: {legitimate_games}")
        print(f"Games with statistics: {games_with_stats}")
        print(f"REAL COVERAGE: {real_coverage:.1f}%")
        print()
        
        if real_coverage >= 85:
            print("✅ Coverage is actually quite good when excluding preseason!")
        else:
            print("⚠️  Still need to collect more statistics for regular/playoff games")
        
        # Write summary to file
        with open("missing_games_analysis.txt", "w") as f:
            f.write(f"Missing Games Analysis\n")
            f.write(f"=====================\n\n")
            f.write(f"Total missing: {len(games_without_stats)}\n")
            f.write(f"Preseason (August): {len(preseason_games)}\n")
            f.write(f"Critical missing (regular/playoff): {len(critical_games)}\n")
            f.write(f"Real coverage: {real_coverage:.1f}%\n\n")
            f.write("Critical missing games:\n")
            for game in critical_games:
                home_team = db.query(Team).filter(Team.team_uid == game.home_team_uid).first()
                away_team = db.query(Team).filter(Team.team_uid == game.away_team_uid).first()
                f.write(f"{away_team.city} {away_team.name} @ {home_team.city} {home_team.name} ({game.game_datetime.date()}) - {game.game_type}\n")
        
        print("📄 Detailed analysis saved to: missing_games_analysis.txt")
        
        return len(critical_games), real_coverage

if __name__ == "__main__":
    critical_count, coverage = analyze_missing_games()
    
    if critical_count > 0:
        print(f"\n🎯 RECOMMENDATION: Focus on collecting {critical_count} critical games")
        print("These are legitimate regular season and playoff games that need statistics")
    else:
        print("\n🎉 All critical games have statistics! Missing games are just preseason.")