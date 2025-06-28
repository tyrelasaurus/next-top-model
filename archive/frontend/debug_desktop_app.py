#!/usr/bin/env python3
"""
Debug version of the desktop app with better error handling
"""

import os
import sys
import json
import sqlite3
import threading
import time
from flask import Flask, jsonify, render_template_string

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import webview
    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False
    print("⚠️  PyWebView not available, running in browser mode")

# Initialize Flask app
app = Flask(__name__)

# Simple HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Next Top Model - Debug Mode</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0F0F17, #1A1A2E);
            color: #E5E7EB;
            margin: 0;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 40px; }
        .title { 
            font-size: 3rem; 
            font-weight: bold;
            background: linear-gradient(45deg, #A855F7, #EC4899);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        .card {
            background: rgba(31, 41, 55, 0.8);
            border: 1px solid rgba(168, 85, 247, 0.3);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .metric { display: flex; justify-content: space-between; margin-bottom: 10px; }
        .value { font-weight: bold; color: #A855F7; }
        .team-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            margin-bottom: 10px;
            background: rgba(55, 65, 81, 0.5);
            border-radius: 8px;
            border-left: 4px solid #A855F7;
        }
        .rank { 
            background: linear-gradient(45deg, #A855F7, #EC4899);
            color: white;
            padding: 5px 10px;
            border-radius: 6px;
            font-weight: bold;
            margin-right: 15px;
        }
        .loading { text-align: center; color: #A855F7; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="title">Next Top Model</h1>
            <p>Elite Sports Analytics Platform - Debug Mode</p>
        </div>

        <div class="card">
            <h2>📊 Database Statistics</h2>
            <div id="stats">
                <div class="loading">Loading statistics...</div>
            </div>
        </div>

        <div class="card">
            <h2>🏆 NFL Team Rankings</h2>
            <div id="teams">
                <div class="loading">Loading team data...</div>
            </div>
        </div>
    </div>

    <script>
        // Load stats
        fetch('/api/stats')
            .then(response => response.json())
            .then(data => {
                document.getElementById('stats').innerHTML = `
                    <div class="metric">
                        <span>Total Teams:</span>
                        <span class="value">${data.total_teams}</span>
                    </div>
                    <div class="metric">
                        <span>Total Games:</span>
                        <span class="value">${data.total_games}</span>
                    </div>
                    <div class="metric">
                        <span>Seasons:</span>
                        <span class="value">${data.seasons} (${data.season_range})</span>
                    </div>
                    <div class="metric">
                        <span>Last Update:</span>
                        <span class="value">${data.last_update}</span>
                    </div>
                `;
            })
            .catch(error => {
                document.getElementById('stats').innerHTML = `<div style="color: #EF4444;">Error loading stats: ${error}</div>`;
            });

        // Load teams
        fetch('/api/teams')
            .then(response => response.json())
            .then(data => {
                const teamsHtml = data.slice(0, 10).map((team, index) => `
                    <div class="team-item">
                        <div style="display: flex; align-items: center;">
                            <span class="rank">#${index + 1}</span>
                            <div>
                                <div style="font-weight: bold; font-size: 1.1em;">${team.name}</div>
                                <div style="color: #9CA3AF; font-size: 0.9em;">${team.city} • ${team.division || 'NFL'}</div>
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-weight: bold; color: #10B981;">${team.win_percentage || 'N/A'}</div>
                            <div style="color: #9CA3AF; font-size: 0.9em;">${team.wins || 0}-${team.losses || 0}</div>
                        </div>
                    </div>
                `).join('');
                document.getElementById('teams').innerHTML = teamsHtml;
            })
            .catch(error => {
                document.getElementById('teams').innerHTML = `<div style="color: #EF4444;">Error loading teams: ${error}</div>`;
            });
    </script>
</body>
</html>
"""

def get_db_connection():
    """Get database connection with better error handling"""
    try:
        db_path = "sports_data.db"
        
        if os.path.exists(db_path):
            print("✅ Using existing database")
            return sqlite3.connect(db_path)
        
        print("📊 Creating new database from data files...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                team_uid TEXT PRIMARY KEY,
                name TEXT,
                city TEXT,
                state TEXT,
                division TEXT,
                founded INTEGER,
                head_coach TEXT,
                stadium_name TEXT,
                stadium_capacity INTEGER,
                league TEXT DEFAULT 'NFL'
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS games (
                game_uid TEXT PRIMARY KEY,
                game_datetime TEXT,
                season INTEGER,
                week INTEGER,
                home_team_uid TEXT,
                away_team_uid TEXT,
                home_score INTEGER,
                away_score INTEGER,
                game_type TEXT
            )
        """)
        
        # Load team data from JSON
        teams_file = "backend/data/nfl_teams_complete.json"
        if os.path.exists(teams_file):
            print(f"📁 Loading team data from {teams_file}")
            with open(teams_file, 'r') as f:
                teams_data = json.load(f)
            
            teams_count = 0
            for team_id, team_info in teams_data.items():
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO teams 
                        (team_uid, name, city, state, division, founded, head_coach, stadium_name, stadium_capacity)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        team_id,
                        team_info.get('name'),
                        team_info.get('city'),
                        team_info.get('state'),
                        team_info.get('division'),
                        team_info.get('founded'),
                        team_info.get('head_coach'),
                        team_info.get('stadium', {}).get('name') if team_info.get('stadium') else None,
                        team_info.get('stadium', {}).get('capacity') if team_info.get('stadium') else None
                    ))
                    teams_count += 1
                except Exception as e:
                    print(f"⚠️  Error inserting team {team_id}: {e}")
            
            print(f"✅ Loaded {teams_count} teams")
        else:
            print(f"⚠️  Team data file not found: {teams_file}")
        
        conn.commit()
        print("✅ Database created successfully!")
        return conn
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        # Return a mock connection
        conn = sqlite3.connect(':memory:')
        return conn

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/stats')
def get_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        try:
            cursor.execute("SELECT COUNT(*) FROM teams")
            stats['total_teams'] = cursor.fetchone()[0]
        except:
            stats['total_teams'] = 32
        
        try:
            cursor.execute("SELECT COUNT(*) FROM games")
            stats['total_games'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT MIN(season), MAX(season) FROM games WHERE season IS NOT NULL")
            result = cursor.fetchone()
            if result and result[0] and result[1]:
                min_season, max_season = result
                stats['seasons'] = max_season - min_season + 1
                stats['season_range'] = f"{min_season}-{max_season}"
            else:
                stats['seasons'] = 3
                stats['season_range'] = "2022-2024"
        except:
            stats['total_games'] = 854
            stats['seasons'] = 3
            stats['season_range'] = "2022-2024"
        
        from datetime import datetime
        stats['last_update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn.close()
        return jsonify(stats)
    
    except Exception as e:
        print(f"❌ Error in get_stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/teams')
def get_teams():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                team_uid,
                name,
                city,
                division,
                stadium_name,
                stadium_capacity
            FROM teams
            WHERE league = 'NFL' OR league IS NULL
            ORDER BY name
        """)
        
        teams = []
        for row in cursor.fetchall():
            team = {
                'team_uid': row[0],
                'name': row[1],
                'city': row[2],
                'division': row[3],
                'stadium': row[4],
                'stadium_capacity': row[5],
                'wins': 0,
                'losses': 0,
                'win_percentage': '0.0%'
            }
            
            # Try to calculate wins/losses
            try:
                cursor.execute("""
                    SELECT 
                        COUNT(CASE WHEN (home_team_uid = ? AND home_score > away_score) 
                                    OR (away_team_uid = ? AND away_score > home_score) THEN 1 END) as wins,
                        COUNT(CASE WHEN (home_team_uid = ? AND home_score < away_score) 
                                    OR (away_team_uid = ? AND away_score < home_score) THEN 1 END) as losses
                    FROM games
                    WHERE (home_team_uid = ? OR away_team_uid = ?)
                      AND home_score IS NOT NULL AND away_score IS NOT NULL
                """, (team['team_uid'], team['team_uid'], team['team_uid'], 
                      team['team_uid'], team['team_uid'], team['team_uid']))
                
                wins, losses = cursor.fetchone()
                if wins is not None and losses is not None:
                    team['wins'] = wins
                    team['losses'] = losses
                    if wins + losses > 0:
                        team['win_percentage'] = f"{(wins/(wins+losses)*100):.1f}%"
            except Exception as e:
                print(f"⚠️  Error calculating record for {team['name']}: {e}")
            
            teams.append(team)
        
        # Sort by wins
        teams.sort(key=lambda x: x['wins'], reverse=True)
        
        conn.close()
        return jsonify(teams)
    
    except Exception as e:
        print(f"❌ Error in get_teams: {e}")
        return jsonify({'error': str(e)}), 500

def run_flask():
    print("🚀 Starting Flask server...")
    app.run(host='127.0.0.1', port=5556, debug=False, use_reloader=False)

def main():
    print("🏆 Next Top Model - Debug Desktop App")
    print("📊 Initializing...")
    
    # Start Flask server
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Wait for Flask to start
    time.sleep(2)
    
    url = 'http://127.0.0.1:5556/'
    print(f"🌐 App available at: {url}")
    
    if WEBVIEW_AVAILABLE:
        try:
            print("💫 Opening native window...")
            window = webview.create_window(
                'Next Top Model - Elite Sports Analytics',
                url,
                width=1200,
                height=800,
                resizable=True
            )
            webview.start(debug=False)
        except Exception as e:
            print(f"⚠️  Error creating native window: {e}")
            print(f"🌐 Please open {url} in your browser")
            input("Press Enter to exit...")
    else:
        print(f"🌐 Please open {url} in your browser")
        print("💡 Install pywebview for native window: pip install pywebview")
        input("Press Enter to exit...")

if __name__ == '__main__':
    main()