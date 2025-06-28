#!/usr/bin/env python3
"""Debug script to understand Pro Football Reference table structure"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def debug_table_structure():
    """Debug the actual table structure on Pro Football Reference"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        url = "https://www.pro-football-reference.com/years/2024/games.htm"
        logger.info(f"Loading page: {url}")
        driver.get(url)
        
        # Wait for table to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "games"))
        )
        
        # Find the games table
        table = driver.find_element(By.ID, "games")
        tbody = table.find_element(By.TAG_NAME, "tbody")
        rows = tbody.find_elements(By.TAG_NAME, "tr")
        
        logger.info(f"Found {len(rows)} rows in table")
        
        # Analyze first few rows
        for i, row in enumerate(rows[:10]):
            th_cells = row.find_elements(By.TAG_NAME, "th")
            td_cells = row.find_elements(By.TAG_NAME, "td")
            
            logger.info(f"\nRow {i}:")
            logger.info(f"  TH cells: {len(th_cells)}")
            logger.info(f"  TD cells: {len(td_cells)}")
            
            if th_cells:
                for j, th in enumerate(th_cells):
                    logger.info(f"    TH[{j}]: '{th.text.strip()}'")
            
            if td_cells:
                for j, td in enumerate(td_cells[:10]):  # First 10 columns
                    logger.info(f"    TD[{j}]: '{td.text.strip()}'")
            
            # Stop after finding a complete game row
            if th_cells and td_cells and len(td_cells) >= 7:
                logger.info("\n=== FOUND COMPLETE GAME ROW ===")
                break
                
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    debug_table_structure()