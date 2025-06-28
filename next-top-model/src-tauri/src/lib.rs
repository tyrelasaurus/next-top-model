use rusqlite::{Connection, Result};
use serde::{Deserialize, Serialize};
use std::path::Path;

#[derive(Debug, Serialize, Deserialize)]
pub struct Team {
    team_uid: String,
    city: Option<String>,
    name: String,
    abbreviation: Option<String>,
    stadium_name: Option<String>,
    stadium_capacity: Option<i32>,
    conference: Option<String>,
    division: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Game {
    game_uid: String,
    season: i32,
    week: Option<f64>,
    game_type: Option<String>,
    home_team_uid: Option<String>,
    away_team_uid: Option<String>,
    game_datetime: Option<String>,
    venue: Option<String>,
    home_score: Option<i32>,
    away_score: Option<i32>,
    overtime: Option<i32>,
    weather_temp: Option<f64>,
    weather_condition: Option<String>,
    attendance: Option<i32>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct TeamGameStat {
    stat_uid: String,
    game_uid: String,
    team_uid: String,
    is_home_team: Option<i32>,
    total_yards: Option<i32>,
    passing_yards: Option<i32>,
    rushing_yards: Option<i32>,
    first_downs: Option<i32>,
    turnovers: Option<i32>,
    penalties: Option<i32>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct TeamSeasonStat {
    stat_uid: String,
    team_uid: String,
    season: i32,
    wins: Option<i32>,
    losses: Option<i32>,
    ties: Option<i32>,
    win_percentage: Option<f64>,
}

fn get_db_connection() -> Result<Connection> {
    let db_path = "/Volumes/Extreme SSD/next_top_model/backend/nfl_data.db";
    
    // Check if file exists
    if !Path::new(db_path).exists() {
        eprintln!("Database file not found at: {}", db_path);
        return Err(rusqlite::Error::SqliteFailure(
            rusqlite::ffi::Error::new(rusqlite::ffi::SQLITE_CANTOPEN),
            Some("Database file not found".to_string())
        ));
    }
    
    let conn = Connection::open(db_path)?;
    
    // Test the connection
    let _: i32 = conn.query_row("SELECT 1", [], |row| row.get(0))?;
    
    Ok(conn)
}

#[tauri::command]
fn get_teams() -> Result<Vec<Team>, String> {
    println!("get_teams called");
    
    let conn = get_db_connection().map_err(|e| {
        println!("Teams: Database connection error: {}", e);
        e.to_string()
    })?;
    
    let mut stmt = conn.prepare("
        SELECT team_uid, city, name, abbreviation, stadium_name, 
               stadium_capacity, conference, division 
        FROM teams 
        ORDER BY conference, division, name
    ").map_err(|e| {
        println!("Teams: Query preparation error: {}", e);
        e.to_string()
    })?;
    
    let team_iter = stmt.query_map([], |row| {
        Ok(Team {
            team_uid: row.get(0)?,
            city: row.get(1)?,
            name: row.get(2)?,
            abbreviation: row.get(3)?,
            stadium_name: row.get(4)?,
            stadium_capacity: row.get(5)?,
            conference: row.get(6)?,
            division: row.get(7)?,
        })
    }).map_err(|e| {
        println!("Teams: Query execution error: {}", e);
        e.to_string()
    })?;
    
    let mut teams = Vec::new();
    for team in team_iter {
        teams.push(team.map_err(|e| {
            println!("Teams: Row processing error: {}", e);
            e.to_string()
        })?);
    }
    
    println!("Retrieved {} teams", teams.len());
    Ok(teams)
}

#[tauri::command]
fn get_games(season: Option<i32>, team_uid: Option<String>) -> Result<Vec<Game>, String> {
    println!("get_games called with season: {:?}, team_uid: {:?}", season, team_uid);
    
    let conn = get_db_connection().map_err(|e| {
        println!("Database connection error: {}", e);
        e.to_string()
    })?;
    
    let mut query = "
        SELECT game_uid, season, week, game_type, home_team_uid, away_team_uid,
               game_datetime, venue, home_score, away_score, overtime, weather_temp, weather_condition, attendance
        FROM games
        WHERE 1=1
    ".to_string();
    
    let mut params: Vec<Box<dyn rusqlite::types::ToSql>> = Vec::new();
    
    if let Some(s) = season {
        query.push_str(" AND season = ?");
        params.push(Box::new(s));
    }
    
    if let Some(team) = team_uid {
        query.push_str(" AND (home_team_uid = ? OR away_team_uid = ?)");
        params.push(Box::new(team.clone()));
        params.push(Box::new(team));
    }
    
    query.push_str(" ORDER BY game_datetime DESC");
    
    println!("Executing query: {}", query);
    
    let mut stmt = conn.prepare(&query).map_err(|e| {
        println!("Query preparation error: {}", e);
        e.to_string()
    })?;
    
    let param_refs: Vec<&dyn rusqlite::types::ToSql> = params.iter().map(|p| p.as_ref()).collect();
    
    let game_iter = stmt.query_map(&param_refs[..], |row| {
        Ok(Game {
            game_uid: row.get(0)?,
            season: row.get(1)?,
            week: row.get(2)?,
            game_type: row.get(3)?,
            home_team_uid: row.get(4)?,
            away_team_uid: row.get(5)?,
            game_datetime: row.get(6)?,
            venue: row.get(7)?,
            home_score: row.get(8)?,
            away_score: row.get(9)?,
            overtime: row.get(10)?,
            weather_temp: row.get(11)?,
            weather_condition: row.get(12)?,
            attendance: row.get(13)?,
        })
    }).map_err(|e| {
        println!("Query execution error: {}", e);
        e.to_string()
    })?;
    
    let mut games = Vec::new();
    for game in game_iter {
        games.push(game.map_err(|e| {
            println!("Row processing error: {}", e);
            e.to_string()
        })?);
    }
    
    println!("Retrieved {} games", games.len());
    Ok(games)
}

#[tauri::command]
fn get_team_season_stats(season: Option<i32>, team_uid: Option<String>) -> Result<Vec<TeamSeasonStat>, String> {
    println!("get_team_season_stats called with season: {:?}, team_uid: {:?}", season, team_uid);
    
    let conn = get_db_connection().map_err(|e| {
        println!("Database connection error: {}", e);
        e.to_string()
    })?;
    
    let mut query = "
        SELECT stat_uid, team_uid, season, wins, losses, ties, win_percentage
        FROM team_season_stats
        WHERE 1=1
    ".to_string();
    
    let mut params: Vec<Box<dyn rusqlite::types::ToSql>> = Vec::new();
    
    if let Some(s) = season {
        query.push_str(" AND season = ?");
        params.push(Box::new(s));
    }
    
    if let Some(team) = team_uid {
        query.push_str(" AND team_uid = ?");
        params.push(Box::new(team));
    }
    
    query.push_str(" ORDER BY season DESC, win_percentage DESC");
    
    println!("Executing query: {}", query);
    
    let mut stmt = conn.prepare(&query).map_err(|e| {
        println!("Query preparation error: {}", e);
        e.to_string()
    })?;
    
    let param_refs: Vec<&dyn rusqlite::types::ToSql> = params.iter().map(|p| p.as_ref()).collect();
    
    let stats_iter = stmt.query_map(&param_refs[..], |row| {
        Ok(TeamSeasonStat {
            stat_uid: row.get(0)?,
            team_uid: row.get(1)?,
            season: row.get(2)?,
            wins: row.get(3)?,
            losses: row.get(4)?,
            ties: row.get(5)?,
            win_percentage: row.get(6)?,
        })
    }).map_err(|e| {
        println!("Query execution error: {}", e);
        e.to_string()
    })?;
    
    let mut stats = Vec::new();
    for stat in stats_iter {
        stats.push(stat.map_err(|e| {
            println!("Row processing error: {}", e);
            e.to_string()
        })?);
    }
    
    println!("Retrieved {} team season stats", stats.len());
    Ok(stats)
}

#[tauri::command]
fn get_team_game_stats(game_uid: Option<String>, team_uid: Option<String>) -> Result<Vec<TeamGameStat>, String> {
    println!("get_team_game_stats called with game_uid: {:?}, team_uid: {:?}", game_uid, team_uid);
    
    let conn = get_db_connection().map_err(|e| {
        println!("Database connection error: {}", e);
        e.to_string()
    })?;
    
    let mut query = "
        SELECT stat_uid, game_uid, team_uid, is_home_team, total_yards, 
               passing_yards, rushing_yards, first_downs, turnovers, penalties
        FROM team_game_stats
        WHERE 1=1
    ".to_string();
    
    let mut params: Vec<Box<dyn rusqlite::types::ToSql>> = Vec::new();
    
    if let Some(game) = game_uid {
        query.push_str(" AND game_uid = ?");
        params.push(Box::new(game));
    }
    
    if let Some(team) = team_uid {
        query.push_str(" AND team_uid = ?");
        params.push(Box::new(team));
    }
    
    query.push_str(" ORDER BY game_uid DESC");
    
    println!("Executing query: {}", query);
    
    let mut stmt = conn.prepare(&query).map_err(|e| {
        println!("Query preparation error: {}", e);
        e.to_string()
    })?;
    
    let param_refs: Vec<&dyn rusqlite::types::ToSql> = params.iter().map(|p| p.as_ref()).collect();
    
    let stats_iter = stmt.query_map(&param_refs[..], |row| {
        Ok(TeamGameStat {
            stat_uid: row.get(0)?,
            game_uid: row.get(1)?,
            team_uid: row.get(2)?,
            is_home_team: row.get(3)?,
            total_yards: row.get(4)?,
            passing_yards: row.get(5)?,
            rushing_yards: row.get(6)?,
            first_downs: row.get(7)?,
            turnovers: row.get(8)?,
            penalties: row.get(9)?,
        })
    }).map_err(|e| {
        println!("Query execution error: {}", e);
        e.to_string()
    })?;
    
    let mut stats = Vec::new();
    for stat in stats_iter {
        stats.push(stat.map_err(|e| {
            println!("Row processing error: {}", e);
            e.to_string()
        })?);
    }
    
    println!("Retrieved {} team game stats", stats.len());
    Ok(stats)
}

#[tauri::command]
fn test_db_connection() -> Result<String, String> {
    let db_path = "/Volumes/Extreme SSD/next_top_model/backend/nfl_data.db";
    
    if !Path::new(db_path).exists() {
        return Ok(format!("Database file not found at: {}", db_path));
    }
    
    match get_db_connection() {
        Ok(conn) => {
            match conn.prepare("SELECT COUNT(*) FROM games") {
                Ok(mut stmt) => {
                    match stmt.query_row([], |row| {
                        let count: i64 = row.get(0)?;
                        Ok(count)
                    }) {
                        Ok(count) => Ok(format!("Database connected successfully. Games count: {}", count)),
                        Err(e) => Ok(format!("Error querying games: {}", e))
                    }
                },
                Err(e) => Ok(format!("Error preparing query: {}", e))
            }
        },
        Err(e) => Ok(format!("Database connection error: {}", e))
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![get_teams, get_games, get_team_season_stats, get_team_game_stats, test_db_connection])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
