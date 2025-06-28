#!/usr/bin/env python3
"""
Debug data sources to understand why matching is failing
"""

import requests
import sys
from pathlib import Path
from datetime import datetime
import json

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.models.sports import Game, Team

def test_espn_api():
    """Test ESPN API to see what data is available"""
    print("=" * 60)
    print("ESPN API TEST")
    print("=" * 60)
    
    # Test current ESPN API
    url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        events = data.get('events', [])
        
        print(f"ESPN API Status: ✅ Success")
        print(f"Events found: {len(events)}")
        
        if events:
            sample_event = events[0]
            print(f"\nSample event structure:")
            print(f"ID: {sample_event.get('id')}")
            print(f"Date: {sample_event.get('date')}")
            print(f"Name: {sample_event.get('name')}")
            print(f"Season: {sample_event.get('season', {}).get('year')}")
            print(f"Week: {sample_event.get('week', {}).get('number')}")
            
            competitions = sample_event.get('competitions', [])
            if competitions:
                comp = competitions[0]
                competitors = comp.get('competitors', [])
                
                print(f"\nTeams:")
                for competitor in competitors:
                    team = competitor.get('team', {})
                    print(f"  {team.get('displayName')} (Home/Away: {competitor.get('homeAway')})")
                
                print(f"\nAvailable data:")
                if comp.get('attendance'):
                    print(f"  Attendance: {comp['attendance']}")
                if comp.get('weather'):
                    print(f"  Weather: {comp['weather']}")
                if comp.get('venue'):
                    print(f"  Venue: {comp['venue'].get('fullName')}")
        
        # Test specific date
        print(f"\n" + "-" * 40)
        print("Testing specific date (2024-09-06):")
        
        date_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=20240906"
        date_response = requests.get(date_url, timeout=10)
        date_response.raise_for_status()
        
        date_data = date_response.json()
        date_events = date_data.get('events', [])
        
        print(f"Events on 2024-09-06: {len(date_events)}")
        
        for event in date_events[:2]:  # Show first 2
            competitions = event.get('competitions', [])
            if competitions:
                comp = competitions[0]
                competitors = comp.get('competitors', [])
                teams = [c.get('team', {}).get('displayName', '') for c in competitors]
                print(f"  {event.get('date')}: {' vs '.join(teams)}")
        
    except Exception as e:
        print(f"ESPN API Error: {e}")

def test_sample_database_game():
    """Test matching with a sample database game"""
    print("\n" + "=" * 60)
    print("DATABASE GAME ANALYSIS")
    print("=" * 60)
    
    with SessionLocal() as db:
        # Get a recent game
        game = db.query(Game).filter(
            Game.season == 2024,
            Game.game_datetime.isnot(None)
        ).first()
        
        if not game:
            print("No suitable game found for testing")
            return
        
        print(f"Sample game: {game.game_uid}")
        print(f"Date: {game.game_datetime}")
        print(f"Season: {game.season}, Week: {game.week}")
        
        # Get team names
        home_team = db.query(Team).filter(Team.team_uid == game.home_team_uid).first()
        away_team = db.query(Team).filter(Team.team_uid == game.away_team_uid).first()
        
        if home_team and away_team:
            print(f"Teams: {away_team.city} {away_team.name} @ {home_team.city} {home_team.name}")
            
            # Test ESPN API for this specific date
            date_str = game.game_datetime.strftime("%Y%m%d")
            url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={date_str}"
            
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                events = data.get('events', [])
                
                print(f"\nESPN events on {date_str}: {len(events)}")
                
                for event in events:
                    competitions = event.get('competitions', [])
                    for comp in competitions:
                        competitors = comp.get('competitors', [])
                        if len(competitors) >= 2:
                            espn_teams = []
                            for competitor in competitors:
                                team_name = competitor.get('team', {}).get('displayName', '')
                                espn_teams.append(team_name)
                            
                            print(f"  ESPN: {' vs '.join(espn_teams)}")
                            
                            # Check for name matches
                            home_match = any(name.lower() in team.lower() for team in espn_teams 
                                           for name in [home_team.city.lower(), home_team.name.lower()])
                            away_match = any(name.lower() in team.lower() for team in espn_teams 
                                           for name in [away_team.city.lower(), away_team.name.lower()])
                            
                            if home_match or away_match:
                                print(f"    ✅ Match found! Home: {home_match}, Away: {away_match}")
                                
                                # Show available data
                                if comp.get('attendance'):
                                    print(f"    Attendance: {comp['attendance']}")
                                if comp.get('weather'):
                                    print(f"    Weather: {comp['weather']}")
                            else:
                                print(f"    ❌ No team match")
                
            except Exception as e:
                print(f"ESPN API Error for specific date: {e}")

def check_data_availability():
    """Check what data we already have vs what we need"""
    print("\n" + "=" * 60)
    print("DATA AVAILABILITY ANALYSIS")
    print("=" * 60)
    
    with SessionLocal() as db:
        total_games = db.query(Game).count()
        
        # Check what data we have
        with_attendance = db.query(Game).filter(Game.attendance.isnot(None)).count()
        with_weather_temp = db.query(Game).filter(Game.weather_temp.isnot(None)).count()
        with_weather_condition = db.query(Game).filter(Game.weather_condition.isnot(None)).count()
        with_venue = db.query(Game).filter(Game.venue.isnot(None)).count()
        
        print(f"Total games: {total_games}")
        print(f"With attendance: {with_attendance} ({with_attendance/total_games*100:.1f}%)")
        print(f"With weather temp: {with_weather_temp} ({with_weather_temp/total_games*100:.1f}%)")
        print(f"With weather condition: {with_weather_condition} ({with_weather_condition/total_games*100:.1f}%)")
        print(f"With venue: {with_venue} ({with_venue/total_games*100:.1f}%)")
        
        # Check by season
        print(f"\nBy season:")
        seasons = db.query(Game.season).distinct().all()
        for (season,) in sorted(seasons):
            season_total = db.query(Game).filter(Game.season == season).count()
            season_attendance = db.query(Game).filter(
                Game.season == season, 
                Game.attendance.isnot(None)
            ).count()
            
            print(f"  {season}: {season_total} games, {season_attendance} with attendance")

def suggest_alternative_approach():
    """Suggest alternative data collection approaches"""
    print("\n" + "=" * 60)
    print("ALTERNATIVE APPROACH SUGGESTIONS")
    print("=" * 60)
    
    print("1. Historical Data Focus:")
    print("   - ESPN API works well for current/recent data")
    print("   - For historical games (2021-2023), consider:")
    print("     a) Pro Football Reference (selective scraping)")
    print("     b) Historical weather APIs using stadium GPS coordinates")
    print("     c) Wikipedia for major games (playoffs)")
    
    print("\n2. Stadium-Based Weather Collection:")
    print("   - Use stadium GPS coordinates from teams table")
    print("   - Query historical weather APIs for game dates")
    print("   - Focus on outdoor stadiums first")
    
    print("\n3. Incremental Strategy:")
    print("   - Phase 1: Current season data from ESPN")
    print("   - Phase 2: Historical weather from coordinates")
    print("   - Phase 3: Selective PFR for playoff games")
    
    print("\n4. Manual Data for Key Games:")
    print("   - Super Bowls and major playoff games")
    print("   - Often well-documented with attendance/weather")
    print("   - High-value, low-volume approach")

if __name__ == "__main__":
    print("NFL DATA SOURCES DIAGNOSTIC")
    print("=" * 80)
    
    test_espn_api()
    test_sample_database_game()
    check_data_availability()
    suggest_alternative_approach()
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)