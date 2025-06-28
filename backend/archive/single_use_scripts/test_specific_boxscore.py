#!/usr/bin/env python3
"""Test the enhanced boxscore scraper with the specific game provided"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backend.boxscore_scraper import BoxscoreScraper
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_specific_game():
    """Test with the specific game: 202409150min"""
    
    # Construct the game ID that would match our database format
    game_id = "NFL_202409150min"
    
    logger.info(f"Testing enhanced scraper with game: {game_id}")
    
    with BoxscoreScraper(headless=False) as scraper:  # Use visible browser for debugging
        
        # Test URL construction
        url = scraper.construct_boxscore_url(game_id)
        logger.info(f"Constructed URL: {url}")
        
        # Scrape the detailed data
        boxscore_data = scraper.scrape_detailed_boxscore(game_id)
        
        if boxscore_data:
            logger.info("✅ Successfully scraped detailed boxscore data")
            
            # Print summary of what we found
            logger.info(f"Game info: {list(boxscore_data.get('game_info', {}).keys())}")
            logger.info(f"Team stats sections: {list(boxscore_data.get('team_stats', {}).keys())}")
            logger.info(f"Scoring plays: {len(boxscore_data.get('scoring_summary', []))}")
            logger.info(f"Player stats sections: {list(boxscore_data.get('player_stats', {}).keys())}")
            
            # Show sample team stats
            team_stats = boxscore_data.get('team_stats', {})
            logger.info(f"\\nSample team stats found:")
            for stat_name, values in list(team_stats.items())[:5]:
                if isinstance(values, dict) and 'away' in values:
                    logger.info(f"  {stat_name}: Away={values['away']}, Home={values['home']}")
                elif isinstance(values, list) and values:
                    logger.info(f"  {stat_name}: {len(values)} entries")
            
            # Show sample scoring plays
            scoring = boxscore_data.get('scoring_summary', [])
            if scoring:
                logger.info(f"\\nSample scoring plays:")
                for play in scoring[:3]:
                    logger.info(f"  Q{play.get('quarter', '?')} {play.get('time', '')} - {play.get('team', '')}: {play.get('description', '')}")
            
            # Save sample data to file for inspection
            with open('sample_boxscore_data.json', 'w') as f:
                json.dump(boxscore_data, f, indent=2)
            logger.info("\\n📁 Full data saved to sample_boxscore_data.json")
            
        else:
            logger.error("❌ Failed to scrape boxscore data")


if __name__ == "__main__":
    test_specific_game()