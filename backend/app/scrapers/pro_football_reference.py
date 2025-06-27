#!/usr/bin/env python3
"""Pro Football Reference scraper for NFL schedule and game data"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
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
            rows = table.find_elements(By.TAG_NAME, "tr")
            
            games = []
            current_week = None
            
            for row in rows[1:]:  # Skip header row
                # Get both td and th elements since first column might be th
                td_cells = row.find_elements(By.TAG_NAME, "td")
                th_cells = row.find_elements(By.TAG_NAME, "th")
                
                # Combine th and td cells, with th cells first (they appear in first column)
                all_cells = th_cells + td_cells
                
                if not all_cells:  # Skip empty rows
                    continue
                
                # Check if this is a week header row (single cell with week info)
                if len(all_cells) == 1 and "Week" in all_cells[0].text:
                    current_week = self._extract_week_number(all_cells[0].text)
                    continue
                
                # Parse game data - need at least 10 columns for a complete game row
                if len(all_cells) >= 10:  # Ensure we have enough columns
                    try:
                        game_data = self._parse_game_row(all_cells, current_week, year)
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
    
    def _parse_game_row(self, cells: List, week: Optional[int], year: int) -> Optional[Dict]:
        """
        Parse a single game row from the schedule table
        
        CORRECTED Column structure with th+td combined:
        0: Week number (as <th> element)
        1: Day (Thu, Sun, etc.)
        2: Date (2022-09-08)
        3: Time (8:20PM)
        4: Winner team (with link)
        5: @ symbol (if away team won)
        6: Loser team (with link)  
        7: boxscore link text
        8: Winner points
        9: Loser points
        10+: Additional stats
        """
        try:
            # Skip rows that don't have game data
            if len(cells) < 10:
                return None
            
            # Extract week from first column if it's a <th> element with number
            current_week = week  # Default to passed week
            first_element = cells[0]
            if first_element.tag_name == 'th' and first_element.text.strip().isdigit():
                current_week = int(first_element.text.strip())
            
            # Extract date from column 2
            date_text = cells[2].text.strip() if len(cells) > 2 else ""
            
            # Extract teams from columns 4 and 6
            winner_team = cells[4].text.strip() if len(cells) > 4 else ""
            loser_team = cells[6].text.strip() if len(cells) > 6 else ""
            
            # Skip if no teams found
            if not winner_team or not loser_team:
                return None
            
            # Check if winner was away team (@ symbol in column 5)
            winner_was_away = cells[5].text.strip() == "@" if len(cells) > 5 else False
            
            # Determine home/away teams
            if winner_was_away:
                away_team = winner_team
                home_team = loser_team
            else:
                home_team = winner_team
                away_team = loser_team
            
            # Get boxscore link for unique game ID from column 7
            boxscore_link = None
            try:
                boxscore_element = cells[7].find_element(By.TAG_NAME, "a")
                boxscore_link = boxscore_element.get_attribute("href")
            except NoSuchElementException:
                pass
            
            # Extract game ID from boxscore link
            game_id = None
            if boxscore_link:
                # Example: /boxscores/202209080ram.htm
                match = re.search(r"/boxscores/(\w+)\.htm", boxscore_link)
                if match:
                    game_id = match.group(1)
            
            # Parse date
            game_date = self._parse_game_date(date_text, year)
            
            # Parse scores from columns 8 and 9
            winner_score = None
            loser_score = None
            try:
                winner_pts = cells[8].text.strip()
                loser_pts = cells[9].text.strip()
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
                "game_id": game_id or f"{year}_{current_week}_{home_team}_{away_team}",
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
        """
        Parse game date from text
        
        CORRECTED: Pro Football Reference uses ISO format dates like "2022-09-08"
        """
        try:
            if not date_text:
                return None
            
            date_text = date_text.strip()
            
            # Try ISO format first (most common on PFR): "2022-09-08"
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
    
    def scrape_game_details(self, boxscore_url: str) -> Optional[Dict]:
        """Scrape detailed game information from boxscore page"""
        if not boxscore_url:
            return None
        
        try:
            logger.info(f"Scraping game details from: {boxscore_url}")
            self.driver.get(boxscore_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Extract additional game details
            game_details = {
                "venue": self._extract_venue(),
                "attendance": self._extract_attendance(),
                "weather": self._extract_weather(),
                "duration": self._extract_duration(),
            }
            
            return game_details
            
        except Exception as e:
            logger.warning(f"Error scraping game details from {boxscore_url}: {e}")
            return None
    
    def _extract_venue(self) -> Optional[str]:
        """Extract venue information from boxscore page"""
        try:
            # Look for venue in game info
            info_elements = self.driver.find_elements(By.CLASS_NAME, "scorebox_meta")
            for element in info_elements:
                text = element.text
                if "Stadium" in text or "Field" in text or "Dome" in text:
                    return text.strip()
        except:
            pass
        return None
    
    def _extract_attendance(self) -> Optional[int]:
        """Extract attendance from boxscore page"""
        try:
            info_elements = self.driver.find_elements(By.CLASS_NAME, "scorebox_meta")
            for element in info_elements:
                text = element.text
                if "Attendance" in text:
                    # Extract number from text like "Attendance: 65,515"
                    match = re.search(r"Attendance:\s*([\d,]+)", text)
                    if match:
                        return int(match.group(1).replace(",", ""))
        except:
            pass
        return None
    
    def _extract_weather(self) -> Optional[str]:
        """Extract weather information from boxscore page"""
        try:
            info_elements = self.driver.find_elements(By.CLASS_NAME, "scorebox_meta")
            for element in info_elements:
                text = element.text
                if "degrees" in text.lower() or "°" in text:
                    return text.strip()
        except:
            pass
        return None
    
    def _extract_duration(self) -> Optional[str]:
        """Extract game duration from boxscore page"""
        try:
            info_elements = self.driver.find_elements(By.CLASS_NAME, "scorebox_meta")
            for element in info_elements:
                text = element.text
                if "Time of Game" in text:
                    match = re.search(r"Time of Game:\s*(\d+:\d+)", text)
                    if match:
                        return match.group(1)
        except:
            pass
        return None