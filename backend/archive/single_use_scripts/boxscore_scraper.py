#!/usr/bin/env python3
"""Enhanced Pro Football Reference boxscore scraper for detailed match data"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.scrapers.pro_football_reference_fixed import ProFootballReferenceScraper
from backend.app.core.database import SessionLocal
from backend.app.models import Game, League
import logging
import re
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BoxscoreScraper(ProFootballReferenceScraper):
    """Enhanced scraper for detailed boxscore data"""
    
    def __init__(self, headless: bool = True):
        super().__init__(headless)
    
    def construct_boxscore_url(self, game_id: str) -> str:
        """
        Construct boxscore URL from game ID
        Game ID format: NFL_202209080ram -> /boxscores/202209080ram.htm
        """
        if game_id.startswith('NFL_'):
            boxscore_id = game_id[4:]  # Remove 'NFL_' prefix
            return f"{self.base_url}/boxscores/{boxscore_id}.htm"
        return None
    
    def scrape_detailed_boxscore(self, game_id: str) -> dict:
        """Scrape detailed boxscore data for a specific game"""
        boxscore_url = self.construct_boxscore_url(game_id)
        if not boxscore_url:
            logger.warning(f"Could not construct URL for game {game_id}")
            return None
            
        logger.info(f"Scraping boxscore: {boxscore_url}")
        
        try:
            self.driver.get(boxscore_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Extract comprehensive game data
            boxscore_data = {
                "game_id": game_id,
                "url": boxscore_url,
                "game_info": self._extract_game_info(),
                "team_stats": self._extract_team_stats(), 
                "scoring_summary": self._extract_scoring_summary(),
                "officials": self._extract_officials(),
                "weather": self._extract_weather_conditions(),
                "game_conditions": self._extract_game_conditions(),
                "attendance": self._extract_attendance_detailed(),
                "player_stats": self._extract_player_stats()
            }
            
            return boxscore_data
            
        except TimeoutException:
            logger.error(f"Timeout loading boxscore: {boxscore_url}")
            return None
        except Exception as e:
            logger.error(f"Error scraping boxscore {boxscore_url}: {e}")
            return None
    
    def _extract_game_info(self) -> dict:
        """Extract basic game information"""
        try:
            game_info = {}
            
            # Get scorebox meta information
            scorebox_meta = self.driver.find_elements(By.CLASS_NAME, "scorebox_meta")
            for meta in scorebox_meta:
                text = meta.text.strip()
                if "Stadium" in text or "Field" in text or "Dome" in text:
                    game_info["venue"] = text
                elif "Attendance" in text:
                    attendance_match = re.search(r"Attendance:\\s*([\\d,]+)", text)
                    if attendance_match:
                        game_info["attendance"] = int(attendance_match.group(1).replace(",", ""))
                elif "Time of Game" in text:
                    time_match = re.search(r"Time of Game:\\s*(\\d+:\\d+)", text)
                    if time_match:
                        game_info["duration"] = time_match.group(1)
                elif "degrees" in text.lower() or "°" in text:
                    game_info["weather"] = text
                    
            return game_info
            
        except Exception as e:
            logger.warning(f"Error extracting game info: {e}")
            return {}
    
    def _extract_team_stats(self) -> dict:
        """Extract team statistics table"""
        try:
            team_stats = {}
            
            # Multiple possible locations for team stats
            possible_ids = ["team_stats", "all_team_stats"]
            
            for table_id in possible_ids:
                try:
                    # Try to find the stats table
                    stats_table = self.driver.find_element(By.ID, table_id)
                    tbody = stats_table.find_element(By.TAG_NAME, "tbody")
                    rows = tbody.find_elements(By.TAG_NAME, "tr")
                    
                    for row in rows:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        th_cells = row.find_elements(By.TAG_NAME, "th")
                        
                        # Handle different table structures
                        if len(cells) >= 3:
                            stat_name = th_cells[0].text.strip() if th_cells else cells[0].text.strip()
                            away_value = cells[1].text.strip() if len(cells) > 1 else ""
                            home_value = cells[2].text.strip() if len(cells) > 2 else ""
                            
                            if stat_name:
                                team_stats[stat_name] = {
                                    "away": away_value,
                                    "home": home_value
                                }
                    
                    if team_stats:  # Found data, break
                        break
                        
                except NoSuchElementException:
                    continue
            
            # Also try to extract advanced stats sections
            advanced_stats = self._extract_advanced_team_stats()
            if advanced_stats:
                team_stats.update(advanced_stats)
            
            return team_stats
            
        except Exception as e:
            logger.warning(f"Error extracting team stats: {e}")
            return {}
            
    def _extract_advanced_team_stats(self) -> dict:
        """Extract advanced team statistics like expected points"""
        try:
            advanced_stats = {}
            
            # Look for expected points table
            try:
                expected_points_table = self.driver.find_element(By.ID, "expected_points")
                advanced_stats["expected_points"] = self._parse_stats_table(expected_points_table)
            except NoSuchElementException:
                pass
            
            # Look for other advanced stat tables
            advanced_table_ids = [
                "player_offense", "player_defense", "home_snap_counts", 
                "vis_snap_counts", "drives", "all_drives"
            ]
            
            for table_id in advanced_table_ids:
                try:
                    table = self.driver.find_element(By.ID, table_id)
                    advanced_stats[table_id] = self._parse_stats_table(table)
                except NoSuchElementException:
                    continue
                    
            return advanced_stats
            
        except Exception as e:
            logger.warning(f"Error extracting advanced team stats: {e}")
            return {}
            
    def _parse_stats_table(self, table) -> list:
        """Parse any statistics table into a structured format"""
        try:
            stats_data = []
            
            # Get headers
            headers = []
            header_rows = table.find_elements(By.XPATH, ".//thead/tr | .//tr[1]")
            if header_rows:
                header_cells = header_rows[0].find_elements(By.TAG_NAME, "th")
                headers = [th.text.strip() for th in header_cells]
            
            # Get data rows
            tbody = table.find_element(By.TAG_NAME, "tbody") if table.find_elements(By.TAG_NAME, "tbody") else table
            rows = tbody.find_elements(By.TAG_NAME, "tr")
            
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                th_cells = row.find_elements(By.TAG_NAME, "th")
                all_cells = th_cells + cells
                
                if all_cells:
                    row_data = {}
                    for i, cell in enumerate(all_cells):
                        header_name = headers[i] if i < len(headers) else f"col_{i}"
                        row_data[header_name] = cell.text.strip()
                    
                    if any(row_data.values()):  # Only add non-empty rows
                        stats_data.append(row_data)
            
            return stats_data
            
        except Exception as e:
            logger.warning(f"Error parsing stats table: {e}")
            return []
    
    def _extract_scoring_summary(self) -> list:
        """Extract quarter-by-quarter scoring summary"""
        try:
            scoring_summary = []
            
            # Look for scoring table
            scoring_table = self.driver.find_element(By.ID, "scoring")
            rows = scoring_table.find_elements(By.TAG_NAME, "tr")
            
            for row in rows[1:]:  # Skip header
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 4:
                    quarter = cells[0].text.strip()
                    time_remaining = cells[1].text.strip()
                    team = cells[2].text.strip()
                    description = cells[3].text.strip()
                    
                    scoring_summary.append({
                        "quarter": quarter,
                        "time": time_remaining,
                        "team": team,
                        "description": description
                    })
            
            return scoring_summary
            
        except NoSuchElementException:
            logger.warning("Scoring summary table not found")
            return []
        except Exception as e:
            logger.warning(f"Error extracting scoring summary: {e}")
            return []
    
    def _extract_officials(self) -> list:
        """Extract game officials"""
        try:
            officials = []
            
            # Look for officials information
            officials_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Officials')]")
            for element in officials_elements:
                # Get parent element text which usually contains the full officials list
                parent_text = element.find_element(By.XPATH, "..").text
                if "Referee:" in parent_text:
                    officials.append(parent_text)
                    break
            
            return officials
            
        except Exception as e:
            logger.warning(f"Error extracting officials: {e}")
            return []
    
    def _extract_weather_conditions(self) -> dict:
        """Extract detailed weather conditions"""
        try:
            weather = {}
            
            # Look for weather information in various locations
            weather_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'degrees') or contains(text(), '°') or contains(text(), 'Wind')]")
            
            for element in weather_elements:
                text = element.text.strip()
                if "degrees" in text.lower() or "°" in text:
                    weather["temperature"] = text
                elif "wind" in text.lower():
                    weather["wind"] = text
                elif "humidity" in text.lower():
                    weather["humidity"] = text
            
            return weather
            
        except Exception as e:
            logger.warning(f"Error extracting weather: {e}")
            return {}
    
    def _extract_game_conditions(self) -> dict:
        """Extract game conditions (surface, indoor/outdoor, etc.)"""
        try:
            conditions = {}
            
            # Look for surface information
            surface_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Grass') or contains(text(), 'Turf') or contains(text(), 'Surface')]")
            for element in surface_elements:
                text = element.text.strip()
                if "grass" in text.lower() or "turf" in text.lower():
                    conditions["surface"] = text
                    
            return conditions
            
        except Exception as e:
            logger.warning(f"Error extracting game conditions: {e}")
            return {}
    
    def _extract_attendance_detailed(self) -> dict:
        """Extract detailed attendance information"""
        try:
            attendance_info = {}
            
            attendance_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Attendance')]")
            for element in attendance_elements:
                text = element.text.strip()
                attendance_match = re.search(r"Attendance:\\s*([\\d,]+)", text)
                if attendance_match:
                    attendance_info["count"] = int(attendance_match.group(1).replace(",", ""))
                    attendance_info["raw_text"] = text
                    
            return attendance_info
            
        except Exception as e:
            logger.warning(f"Error extracting attendance: {e}")
            return {}
    
    def _extract_player_stats(self) -> dict:
        """Extract player statistics tables"""
        try:
            player_stats = {}
            
            # Common player stat table IDs on Pro Football Reference
            stat_tables = [
                "passing", "rushing", "receiving", "defense", 
                "kicking", "punting", "kick_ret", "punt_ret"
            ]
            
            for table_id in stat_tables:
                try:
                    table = self.driver.find_element(By.ID, table_id)
                    player_stats[table_id] = self._parse_player_table(table)
                except NoSuchElementException:
                    continue  # Table doesn't exist for this game
                    
            return player_stats
            
        except Exception as e:
            logger.warning(f"Error extracting player stats: {e}")
            return {}
    
    def _parse_player_table(self, table) -> list:
        """Parse a player statistics table"""
        try:
            stats = []
            rows = table.find_elements(By.TAG_NAME, "tr")
            
            # Get headers
            header_row = rows[0] if rows else None
            headers = []
            if header_row:
                headers = [th.text.strip() for th in header_row.find_elements(By.TAG_NAME, "th")]
            
            # Get data rows
            for row in rows[1:]:
                cells = row.find_elements(By.TAG_NAME, "td")
                if cells:
                    row_data = {}
                    for i, cell in enumerate(cells):
                        if i < len(headers):
                            row_data[headers[i]] = cell.text.strip()
                    if row_data:
                        stats.append(row_data)
            
            return stats
            
        except Exception as e:
            logger.warning(f"Error parsing player table: {e}")
            return []


def test_boxscore_scraper():
    """Test the boxscore scraper with sample games"""
    db = SessionLocal()
    
    try:
        # Get a few sample games
        sample_games = db.query(Game).filter(
            Game.league == League.NFL,
            Game.source == 'pro_football_reference'
        ).limit(3).all()
        
        logger.info(f"Testing boxscore scraper with {len(sample_games)} games")
        
        with BoxscoreScraper(headless=True) as scraper:
            for game in sample_games:
                logger.info(f"\\nTesting game: {game.game_uid}")
                logger.info(f"Teams: {game.away_team.name if game.away_team else 'Unknown'} @ {game.home_team.name if game.home_team else 'Unknown'}")
                
                boxscore_url = scraper.construct_boxscore_url(game.game_uid)
                logger.info(f"Constructed URL: {boxscore_url}")
                
                # Test scraping (but don't save yet)
                boxscore_data = scraper.scrape_detailed_boxscore(game.game_uid)
                
                if boxscore_data:
                    logger.info("✅ Successfully scraped boxscore data")
                    logger.info(f"   Game info keys: {list(boxscore_data.get('game_info', {}).keys())}")
                    logger.info(f"   Team stats available: {len(boxscore_data.get('team_stats', {}))}")
                    logger.info(f"   Scoring plays: {len(boxscore_data.get('scoring_summary', []))}")
                else:
                    logger.warning("❌ Failed to scrape boxscore data")
                    
                # Be respectful to the server
                time.sleep(2)
                
    except Exception as e:
        logger.error(f"Error during testing: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    test_boxscore_scraper()