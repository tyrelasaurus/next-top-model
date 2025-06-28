export enum League {
  NFL = "NFL",
  CFL = "CFL", 
  NCAA = "NCAA"
}

export interface Team {
  team_uid: string;
  league: League;
  city: string;
  name: string;
  abbreviation?: string;
  stadium_name?: string;
  stadium_capacity?: number;
  latitude?: number;
  longitude?: number;
  founded_year?: number;
  conference?: string;
  division?: string;
  created_at: string;
  updated_at: string;
}

export interface Game {
  game_uid: string;
  league: League;
  season: number;
  week?: number;
  game_type?: string;
  home_team_uid: string;
  away_team_uid: string;
  home_team?: Team;
  away_team?: Team;
  game_datetime: string;
  location?: string;
  venue?: string;
  home_score?: number;
  away_score?: number;
  overtime?: number;
  weather_temp?: number;
  weather_condition?: string;
  weather_wind_speed?: number;
  attendance?: number;
  created_at: string;
  updated_at: string;
}

export interface Player {
  player_uid: string;
  name: string;
  first_name?: string;
  last_name?: string;
  position?: string;
  jersey_number?: number;
  birthdate?: string;
  height_inches?: number;
  weight_lbs?: number;
  college?: string;
  draft_year?: number;
  draft_round?: number;
  draft_pick?: number;
  team_uid?: string;
  team?: Team;
  team_history?: TeamHistory[];
  created_at: string;
  updated_at: string;
}

export interface TeamHistory {
  team_uid: string;
  start_date: string;
  end_date?: string;
}

export interface PlayerStat {
  stat_uid: string;
  player_uid: string;
  game_uid: string;
  player?: Player;
  game?: Game;
  
  // Passing stats
  pass_attempts?: number;
  pass_completions?: number;
  pass_yards?: number;
  pass_touchdowns?: number;
  pass_interceptions?: number;
  pass_rating?: number;
  
  // Rushing stats
  rush_attempts?: number;
  rush_yards?: number;
  rush_touchdowns?: number;
  rush_long?: number;
  
  // Receiving stats
  receptions?: number;
  receiving_yards?: number;
  receiving_touchdowns?: number;
  receiving_targets?: number;
  
  // Defensive stats
  tackles?: number;
  sacks?: number;
  interceptions?: number;
  forced_fumbles?: number;
  fumble_recoveries?: number;
  
  // Special teams
  field_goals_made?: number;
  field_goals_attempted?: number;
  extra_points_made?: number;
  punts?: number;
  punt_yards?: number;
  
  // General
  fumbles?: number;
  fumbles_lost?: number;
  
  created_at: string;
  updated_at: string;
}

export interface SearchFilters {
  league?: League;
  season?: number;
  week?: number;
  team_uid?: string;
  player_uid?: string;
  date_from?: string;
  date_to?: string;
  search_text?: string;
}