import httpx
from typing import List, Dict, Optional
from datetime import datetime
import logging

from ..core.config import settings
from ..models import League

logger = logging.getLogger(__name__)


class TheSportsDBClient:
    BASE_URL = "https://www.thesportsdb.com/api/v2/json"
    
    def __init__(self):
        self.api_key = settings.THESPORTSDB_API_KEY
        if not self.api_key:
            raise ValueError("TheSportsDB API key not found in settings")
        
        # Set up headers with API key
        self.headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        self.client = httpx.Client(timeout=30.0, headers=self.headers)
    
    def _get(self, endpoint: str) -> Dict:
        """Make GET request to TheSportsDB API v2"""
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error fetching from TheSportsDB: {e}")
            raise
    
    def get_all_teams(self, league_name: str) -> List[Dict]:
        """Get all teams for a specific league"""
        # Map our league enum to TheSportsDB league IDs
        league_mapping = {
            "NFL": "4391",  # NFL league ID
            "CFL": "4196",  # CFL league ID
            "NCAA": "4479"  # NCAA Division I FBS
        }
        
        league_id = league_mapping.get(league_name)
        if not league_id:
            raise ValueError(f"Unsupported league: {league_name}")
        
        # Use v2 API list endpoint
        result = self._get(f"list/teams/{league_id}")
        # v2 API returns teams in "list" key
        return result.get("list", []) if result else []
    
    def get_team_details(self, team_id: str) -> Optional[Dict]:
        """Get detailed information for a specific team"""
        result = self._get(f"lookup/team/{team_id}")
        teams = result.get("teams", [])
        return teams[0] if teams else None
    
    def get_schedule(self, league_id: str, season: str) -> List[Dict]:
        """Get complete schedule for a league and season using V2 API"""
        # For NFL: league_id = 4391, season format = just year e.g. "2023"
        # Note: NFL seasons on TheSportsDB use single year format (starting year)
        
        # Extract just the year if a range was provided
        if "-" in season:
            season = season.split("-")[0]
            logger.info(f"Converted season format to single year: {season}")
        
        logger.info(f"Getting complete season schedule from TheSportsDB V2 API: {league_id}/{season}")
        
        try:
            # Use V2 API for complete historical season schedule
            result = self._get(f"schedule/league/{league_id}/{season}")
            if result:
                # Check for different possible event keys
                for key in ['schedule', 'events', 'list']:
                    if result.get(key) and isinstance(result[key], list):
                        logger.info(f"Found {len(result[key])} events in '{key}' field for {season} season")
                        return result[key]
                
                # Log unexpected structure
                logger.warning(f"Unexpected V2 API response structure: {list(result.keys())}")
                
        except Exception as e:
            logger.error(f"V2 API schedule endpoint failed: {e}")
            pass
        
        # Fallback to previous events (gets recent games only)
        try:
            logger.info("Falling back to previous events endpoint")
            result = self._get(f"schedule/previous/league/{league_id}")
            events = result.get("schedule", []) if result else []
            logger.info(f"Retrieved {len(events)} recent events from fallback")
            return events
        except Exception as e:
            logger.error(f"Fallback endpoint also failed: {e}")
            return []
    
    def get_past_events(self, team_id: str, limit: int = 10) -> List[Dict]:
        """Get past events for a team"""
        result = self._get(f"schedule/previous/team/{team_id}")
        events = result.get("events", []) if result else []
        return events[:limit]
    
    def get_event_details(self, event_id: str) -> Optional[Dict]:
        """Get detailed information for a specific event/game"""
        result = self._get(f"lookup/event/{event_id}")
        events = result.get("events", [])
        return events[0] if events else None
    
    def get_event_stats(self, event_id: str) -> List[Dict]:
        """Get statistics for a specific event/game"""
        result = self._get(f"lookup/event_stats/{event_id}")
        return result.get("eventstats", []) if result else []
    
    def get_players_by_team(self, team_id: str) -> List[Dict]:
        """Get all players for a team"""
        result = self._get(f"list/players/{team_id}")
        return result.get("player", []) if result else []
    
    def get_player_details(self, player_id: str) -> Optional[Dict]:
        """Get detailed information for a specific player"""
        result = self._get(f"lookup/player/{player_id}")
        players = result.get("players", [])
        return players[0] if players else None
    
    def transform_team_data(self, tsdb_team: Dict, league: League) -> Dict:
        """Transform TheSportsDB team data to our schema"""
        return {
            "team_uid": f"{league.value}_{tsdb_team['idTeam']}",
            "league": league,
            "city": self._extract_city(tsdb_team.get("strTeam", "")),
            "name": tsdb_team.get("strTeam", ""),
            "abbreviation": tsdb_team.get("strTeamShort"),
            "stadium_name": tsdb_team.get("strStadium"),
            "stadium_capacity": int(tsdb_team["intStadiumCapacity"]) if tsdb_team.get("intStadiumCapacity") else None,
            "founded_year": int(tsdb_team["intFormedYear"]) if tsdb_team.get("intFormedYear") else None,
            "conference": tsdb_team.get("strDescriptionEN", "").split(" Conference")[0] if "Conference" in tsdb_team.get("strDescriptionEN", "") else None,
            "source": "thesportsdb"
        }
    
    def transform_game_data(self, tsdb_event: Dict, league: League) -> Dict:
        """Transform TheSportsDB event data to our schema"""
        game_datetime = None
        if tsdb_event.get("dateEvent") and tsdb_event.get("strTime"):
            try:
                # TheSportsDB uses format: "2023-09-07" and "20:20:00" 
                datetime_str = f"{tsdb_event['dateEvent']} {tsdb_event['strTime']}"
                game_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
            except:
                pass
        
        # Extract season from strSeason or dateEvent
        season = None
        if tsdb_event.get("strSeason"):
            try:
                season = int(tsdb_event["strSeason"])
            except:
                pass
        elif tsdb_event.get("dateEvent"):
            try:
                # Extract year from date
                year = datetime.strptime(tsdb_event["dateEvent"], "%Y-%m-%d").year
                # NFL seasons typically start in September and end in February of the following year
                if datetime.strptime(tsdb_event["dateEvent"], "%Y-%m-%d").month <= 6:
                    season = year - 1  # Games in Jan-June are from previous season
                else:
                    season = year
            except:
                pass
        
        return {
            "game_uid": f"{league.value}_{tsdb_event['idEvent']}",
            "league": league,
            "season": season,
            "week": self._extract_week(tsdb_event.get("intRound")),
            "home_team_uid": f"{league.value}_{tsdb_event['idHomeTeam']}" if tsdb_event.get("idHomeTeam") else None,
            "away_team_uid": f"{league.value}_{tsdb_event['idAwayTeam']}" if tsdb_event.get("idAwayTeam") else None,
            "game_datetime": game_datetime,
            "venue": tsdb_event.get("strVenue"),
            "home_score": int(tsdb_event["intHomeScore"]) if tsdb_event.get("intHomeScore") and tsdb_event["intHomeScore"] else None,
            "away_score": int(tsdb_event["intAwayScore"]) if tsdb_event.get("intAwayScore") and tsdb_event["intAwayScore"] else None,
            "source": "thesportsdb"
        }
    
    def transform_player_data(self, tsdb_player: Dict, team_uid: str) -> Dict:
        """Transform TheSportsDB player data to our schema"""
        birthdate = None
        if tsdb_player.get("dateBorn"):
            try:
                birthdate = datetime.strptime(tsdb_player["dateBorn"], "%Y-%m-%d")
            except:
                pass
        
        # Extract height and weight from string format
        height_inches = self._parse_height(tsdb_player.get("strHeight"))
        weight_lbs = self._parse_weight(tsdb_player.get("strWeight"))
        
        return {
            "player_uid": f"PLAYER_{tsdb_player['idPlayer']}",
            "name": tsdb_player.get("strPlayer", ""),
            "position": tsdb_player.get("strPosition"),
            "jersey_number": int(tsdb_player["strNumber"]) if tsdb_player.get("strNumber") else None,
            "birthdate": birthdate,
            "height_inches": height_inches,
            "weight_lbs": weight_lbs,
            "college": tsdb_player.get("strCollege"),
            "team_uid": team_uid,
            "source": "thesportsdb"
        }
    
    def _extract_city(self, team_name: str) -> str:
        """Extract city from team name (e.g., 'Dallas Cowboys' -> 'Dallas')"""
        # Handle special cases for NFL teams
        special_cases = {
            "New England Patriots": "New England",
            "New York Jets": "New York",
            "New York Giants": "New York",
            "Tampa Bay Buccaneers": "Tampa Bay",
            "Green Bay Packers": "Green Bay",
            "Las Vegas Raiders": "Las Vegas",
            "Kansas City Chiefs": "Kansas City",
            "San Francisco 49ers": "San Francisco",
            "Los Angeles Rams": "Los Angeles",
            "Los Angeles Chargers": "Los Angeles",
        }
        
        if team_name in special_cases:
            return special_cases[team_name]
        
        # For other teams, take the first word
        parts = team_name.split()
        if len(parts) > 1:
            return parts[0]
        return team_name
    
    def _extract_week(self, round_str: Optional[str]) -> Optional[int]:
        """Extract week number from round string"""
        if not round_str:
            return None
        try:
            return int(round_str)
        except:
            return None
    
    def _parse_height(self, height_str: Optional[str]) -> Optional[int]:
        """Parse height string (e.g., '6 ft 2 in') to inches"""
        if not height_str:
            return None
        try:
            # Example: "6 ft 2 in" or "1.88 m"
            if "ft" in height_str:
                parts = height_str.split()
                feet = int(parts[0])
                inches = int(parts[2]) if len(parts) > 2 else 0
                return feet * 12 + inches
            elif "m" in height_str:
                meters = float(height_str.replace("m", "").strip())
                return int(meters * 39.37)  # Convert meters to inches
        except:
            pass
        return None
    
    def _parse_weight(self, weight_str: Optional[str]) -> Optional[int]:
        """Parse weight string (e.g., '225 lbs') to pounds"""
        if not weight_str:
            return None
        try:
            if "lbs" in weight_str:
                return int(weight_str.replace("lbs", "").strip())
            elif "kg" in weight_str:
                kg = float(weight_str.replace("kg", "").strip())
                return int(kg * 2.205)  # Convert kg to lbs
        except:
            pass
        return None
    
    def close(self):
        """Close HTTP client"""
        self.client.close()