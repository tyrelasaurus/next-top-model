use rusqlite::{Connection, Result};
use serde::{Deserialize, Serialize};

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
    week: Option<i32>,
    game_type: Option<String>,
    home_team_uid: Option<String>,
    away_team_uid: Option<String>,
    game_datetime: Option<String>,
    venue: Option<String>,
    home_score: Option<i32>,
    away_score: Option<i32>,
    overtime: Option<i32>,
}

fn get_db_connection() -> Result<Connection> {
    let db_path = "/Volumes/Extreme SSD/next_top_model/backend/nfl_data.db";
    Connection::open(db_path)
}

#[tauri::command]
fn get_teams() -> Result<Vec<Team>, String> {
    let conn = get_db_connection().map_err(|e| e.to_string())?;
    
    let mut stmt = conn.prepare("
        SELECT team_uid, city, name, abbreviation, stadium_name, 
               stadium_capacity, conference, division 
        FROM teams 
        ORDER BY conference, division, name
    ").map_err(|e| e.to_string())?;
    
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
    }).map_err(|e| e.to_string())?;
    
    let mut teams = Vec::new();
    for team in team_iter {
        teams.push(team.map_err(|e| e.to_string())?);
    }
    
    Ok(teams)
}

#[tauri::command]
fn get_games(season: Option<i32>, team_uid: Option<String>) -> Result<Vec<Game>, String> {
    let conn = get_db_connection().map_err(|e| e.to_string())?;
    
    let mut query = "
        SELECT game_uid, season, week, game_type, home_team_uid, away_team_uid,
               game_datetime, venue, home_score, away_score, overtime
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
    
    let mut stmt = conn.prepare(&query).map_err(|e| e.to_string())?;
    
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
        })
    }).map_err(|e| e.to_string())?;
    
    let mut games = Vec::new();
    for game in game_iter {
        games.push(game.map_err(|e| e.to_string())?);
    }
    
    Ok(games)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![get_teams, get_games])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
