#!/usr/bin/env python3
"""Pro Football Reference scraper for NFL schedule and game data - FIXED VERSION"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class ProFootballReferenceScraper:
    def __init__(self, headless: bool = True):
        """Initialize the scraper with Chrome WebDriver"""
        self.base_url = "https://www.pro-football-reference.com"
        self.driver = None
        self.headless = headless
        self._setup_driver()
    
    def _setup_driver(self):
        """Set up Chrome WebDriver with options"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            raise
    
    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")
    
    def get_week_schedule(self, season: int, week: int) -> List[Dict]:
        """Get games for a specific week"""
        season_games = self.scrape_season_schedule(season)
        return [game for game in season_games if game.get('week') == week]
    
    def get_playoff_games(self, season: int, round_name: str) -> List[Dict]:
        """Get playoff games for a specific round"""
        # Playoff games are typically in the next calendar year
        playoff_year = season + 1
        
        # Map round names to game types
        round_mapping = {
            "Wild Card": "wildcard",
            "Divisional": "divisional", 
            "Conference Championships": "conference",
            "Super Bowl": "superbowl"
        }
        
        game_type = round_mapping.get(round_name, "playoff")
        
        # Get all games for the season and filter for playoffs
        all_games = self.scrape_season_schedule(season)
        playoff_games = []
        
        for game in all_games:
            # Check if game is in playoff timeframe (typically Jan-Feb)
            game_date = game.get('date', '')
            if game_date and (game_date.startswith(f"{playoff_year}-01") or game_date.startswith(f"{playoff_year}-02")):
                # Determine playoff type based on date and context
                if "wildcard" in game.get('game_type', '').lower() or (game_date.startswith(f"{playoff_year}-01") and "15" <= game_date.split('-')[2] <= "22"):
                    game['game_type'] = 'wildcard'
                elif "divisional" in game.get('game_type', '').lower() or (game_date.startswith(f"{playoff_year}-01") and "25" <= game_date.split('-')[2] <= "31"):
                    game['game_type'] = 'divisional'
                elif "conference" in game.get('game_type', '').lower() or (game_date.startswith(f"{playoff_year}-01") and game_date.split('-')[2] >= "28"):
                    game['game_type'] = 'conference'
                elif "super" in game.get('game_type', '').lower() or game_date.startswith(f"{playoff_year}-02"):
                    game['game_type'] = 'superbowl'
                
                if game.get('game_type') == game_type:
                    playoff_games.append(game)
        
        return playoff_games
    
    def get_game_boxscore(self, game_id: str) -> Optional[Dict]:
        """Get detailed boxscore data for a specific game"""
        # Extract year and game info from game_id (format: NFL_YYYYMMDDTEM)
        try:
            parts = game_id.split('_')
            if len(parts) >= 2:
                date_team = parts[1]
                year = date_team[:4]
                month = date_team[4:6]
                day = date_team[6:8]
                team = date_team[8:]
                
                # Construct boxscore URL
                boxscore_url = f"{self.base_url}/boxscores/{year}{month}{day}0{team}.htm"
                
                logger.info(f"Fetching boxscore from: {boxscore_url}")
                self.driver.get(boxscore_url)
                
                # Wait for page to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "scorebox"))
                )
                
                # Extract basic game info
                boxscore_data = {
                    "game_id": game_id,
                    "url": boxscore_url,
                    "collected_at": datetime.utcnow().isoformat()
                }
                
                # Extract team stats if available
                try:
                    team_stats_table = self.driver.find_element(By.ID, "team_stats")
                    # Parse team statistics table
                    boxscore_data["team_stats"] = self._parse_team_stats_table(team_stats_table)
                except NoSuchElementException:
                    logger.warning(f"No team stats table found for {game_id}")
                
                return boxscore_data
                
        except Exception as e:
            logger.error(f"Failed to get boxscore for {game_id}: {e}")
            return None
    
    def get_game_player_stats(self, game_id: str) -> Optional[Dict]:
        """Get player statistics for a specific game"""
        try:
            # This would require navigating to the boxscore page first
            boxscore_data = self.get_game_boxscore(game_id)
            if not boxscore_data:
                return None
                
            player_stats = {
                "game_id": game_id,
                "passing": [],
                "rushing": [],
                "receiving": [],
                "defense": []
            }
            
            # Extract player stat tables
            stat_tables = [
                ("passing", "#passing"),
                ("rushing", "#rushing"), 
                ("receiving", "#receiving"),
                ("defense", "#defense")
            ]
            
            for stat_type, selector in stat_tables:
                try:
                    table = self.driver.find_element(By.CSS_SELECTOR, selector)
                    player_stats[stat_type] = self._parse_player_stats_table(table)
                except NoSuchElementException:
                    logger.debug(f"No {stat_type} table found for {game_id}")
            
            return player_stats
            
        except Exception as e:
            logger.error(f"Failed to get player stats for {game_id}: {e}")
            return None
    
    def _parse_team_stats_table(self, table) -> Dict:
        """Parse team statistics table"""
        stats = {}
        try:
            rows = table.find_elements(By.TAG_NAME, "tr")
            for row in rows[1:]:  # Skip header
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 3:
                    stat_name = cells[0].text.strip()
                    away_value = cells[1].text.strip()
                    home_value = cells[2].text.strip()
                    stats[stat_name] = {"away": away_value, "home": home_value}
        except Exception as e:
            logger.error(f"Error parsing team stats table: {e}")
        return stats
    
    def _parse_player_stats_table(self, table) -> List[Dict]:
        """Parse player statistics table"""
        players = []
        try:
            rows = table.find_elements(By.TAG_NAME, "tr")
            if len(rows) < 2:
                return players
                
            # Get headers
            header_row = rows[0]
            headers = [th.text.strip() for th in header_row.find_elements(By.TAG_NAME, "th")]
            
            # Parse data rows
            for row in rows[1:]:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= len(headers):
                    player_data = {}
                    for i, header in enumerate(headers):
                        if i < len(cells):
                            player_data[header] = cells[i].text.strip()
                    if player_data:
                        players.append(player_data)
        except Exception as e:
            logger.error(f"Error parsing player stats table: {e}")
        return players
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def scrape_season_schedule(self, year: int) -> List[Dict]:
        """Scrape the complete schedule for a given NFL season"""
        url = f"{self.base_url}/years/{year}/games.htm"
        logger.info(f"Scraping {year} NFL season from: {url}")
        
        try:
            self.driver.get(url)
            
            # Wait for the table to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "games"))
            )
            
            # Find the games table
            table = self.driver.find_element(By.ID, "games")
            tbody = table.find_element(By.TAG_NAME, "tbody")
            rows = tbody.find_elements(By.TAG_NAME, "tr")
            
            games = []
            current_week = None
            
            for row in rows:
                # Get both th and td elements
                th_cells = row.find_elements(By.TAG_NAME, "th")
                td_cells = row.find_elements(By.TAG_NAME, "td")
                
                # Skip rows without data
                if not th_cells and not td_cells:
                    continue
                
                # Check if this is a week header row
                if th_cells and len(td_cells) == 0:
                    week_text = th_cells[0].text.strip()
                    if "Week" in week_text:
                        current_week = self._extract_week_number(week_text)
                        continue
                
                # Parse game data rows (should have both th and td elements)
                if th_cells and td_cells and len(td_cells) >= 9:
                    try:
                        game_data = self._parse_game_row(th_cells, td_cells, current_week, year)
                        if game_data:
                            games.append(game_data)
                    except Exception as e:
                        logger.warning(f"Error parsing game row: {e}")
                        continue
            
            logger.info(f"Successfully scraped {len(games)} games for {year} season")
            return games
            
        except TimeoutException:
            logger.error(f"Timeout waiting for page to load: {url}")
            return []
        except Exception as e:
            logger.error(f"Error scraping {year} season: {e}")
            return []
    
    def _extract_week_number(self, week_text: str) -> Optional[int]:
        """Extract week number from week header text"""
        try:
            # Handle different week formats: "Week 1", "Wild Card", "Divisional", etc.
            if "Week" in week_text:
                match = re.search(r"Week (\d+)", week_text)
                if match:
                    return int(match.group(1))
            elif "Wild Card" in week_text:
                return 19  # NFL playoff week numbering
            elif "Divisional" in week_text:
                return 20
            elif "Conference" in week_text:
                return 21
            elif "Super Bowl" in week_text:
                return 22
            else:
                # Try to extract any number from the text
                match = re.search(r"(\d+)", week_text)
                if match:
                    return int(match.group(1))
        except:
            pass
        return None
    
    def _parse_game_row(self, th_cells: List, td_cells: List, week: Optional[int], year: int) -> Optional[Dict]:
        """
        Parse a single game row from the schedule table
        
        Table structure based on debug output:
        TH[0]: Week number (1, 2, 3...)
        TD[0]: Day (Thu, Sun, etc.)
        TD[1]: Date (2024-09-05)
        TD[2]: Time (8:20PM)
        TD[3]: Winner team
        TD[4]: @ symbol (empty if home team won)
        TD[5]: Loser team  
        TD[6]: boxscore link text
        TD[7]: Winner points
        TD[8]: Loser points
        TD[9+]: Additional stats
        """
        try:
            # Extract week from TH element
            current_week = week  # Default to passed week
            if th_cells and th_cells[0].text.strip().isdigit():
                current_week = int(th_cells[0].text.strip())
            
            # Extract date from TD[1]
            date_text = td_cells[1].text.strip() if len(td_cells) > 1 else ""
            
            # Extract teams from TD[3] and TD[5]
            winner_team = td_cells[3].text.strip() if len(td_cells) > 3 else ""
            loser_team = td_cells[5].text.strip() if len(td_cells) > 5 else ""
            
            # Skip if no teams found
            if not winner_team or not loser_team:
                return None
            
            # Check if winner was away team (@ symbol in TD[4])
            winner_was_away = (len(td_cells) > 4 and td_cells[4].text.strip() == "@")
            
            # Determine home/away teams
            if winner_was_away:
                away_team = winner_team
                home_team = loser_team
            else:
                home_team = winner_team
                away_team = loser_team
            
            # Get boxscore link for unique game ID from TD[6]
            boxscore_link = None
            game_id = None
            try:
                if len(td_cells) > 6:
                    boxscore_element = td_cells[6].find_element(By.TAG_NAME, "a")
                    boxscore_link = boxscore_element.get_attribute("href")
                    # Extract game ID from boxscore link
                    match = re.search(r"/boxscores/(\w+)\.htm", boxscore_link)
                    if match:
                        game_id = match.group(1)
            except:
                pass
            
            # Parse date
            game_date = self._parse_game_date(date_text, year)
            
            # Parse scores from TD[7] and TD[8]
            winner_score = None
            loser_score = None
            try:
                winner_pts = td_cells[7].text.strip() if len(td_cells) > 7 else ""
                loser_pts = td_cells[8].text.strip() if len(td_cells) > 8 else ""
                if winner_pts.isdigit():
                    winner_score = int(winner_pts)
                if loser_pts.isdigit():
                    loser_score = int(loser_pts)
            except (ValueError, IndexError):
                pass
            
            # Assign scores to home/away based on who won
            if winner_was_away:
                away_score = winner_score
                home_score = loser_score
            else:
                home_score = winner_score
                away_score = loser_score
            
            return {
                "game_id": game_id or f"{year}_{current_week}_{home_team.replace(' ', '')}_{away_team.replace(' ', '')}",
                "season": year,
                "week": current_week,
                "date": game_date,
                "home_team": home_team,
                "away_team": away_team,
                "home_score": home_score,
                "away_score": away_score,
                "boxscore_url": boxscore_link,
                "source": "pro_football_reference"
            }
            
        except Exception as e:
            logger.warning(f"Error parsing game row: {e}")
            return None
    
    def _parse_game_date(self, date_text: str, year: int) -> Optional[datetime]:
        """Parse game date from text"""
        try:
            if not date_text:
                return None
            
            date_text = date_text.strip()
            
            # Try ISO format first (Pro Football Reference format): "2024-09-05"
            if re.match(r"\d{4}-\d{2}-\d{2}", date_text):
                return datetime.strptime(date_text, "%Y-%m-%d")
            
            # Try other potential formats as fallback
            formats = [
                "%B %d",  # "September 5"
                "%b %d",   # "Sep 5"
                "%m/%d",   # "9/5"
            ]
            
            for fmt in formats:
                try:
                    parsed_date = datetime.strptime(date_text, fmt)
                    # Add the year
                    return parsed_date.replace(year=year)
                except ValueError:
                    continue
            
            logger.warning(f"Could not parse date: {date_text}")
            return None
            
        except Exception as e:
            logger.warning(f"Error parsing date '{date_text}': {e}")
            return None
    
    def scrape_multiple_seasons(self, years: List[int]) -> Dict[int, List[Dict]]:
        """Scrape multiple seasons of NFL data"""
        all_seasons = {}
        
        for year in years:
            logger.info(f"Starting scrape for {year} season...")
            season_games = self.scrape_season_schedule(year)
            all_seasons[year] = season_games
            
            # Be respectful to the server
            time.sleep(2)
        
        total_games = sum(len(games) for games in all_seasons.values())
        logger.info(f"Completed scraping {len(years)} seasons with {total_games} total games")
        
        return all_seasons