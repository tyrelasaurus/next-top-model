#!/usr/bin/env python3
"""
Fix playoff game categorization in existing data
Categorizes playoff games based on date patterns
"""

import sys
from pathlib import Path
import logging
from datetime import datetime

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.models.sports import Game

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def categorize_playoff_game(game_date: str) -> str:
    """
    Categorize playoff game based on date
    
    Playoff schedule patterns:
    - Wild Card: Mid-January (13-16)
    - Divisional: Late January (20-22) 
    - Conference: End of January (28-29)
    - Super Bowl: Early February (10-15)
    """
    try:
        date_parts = game_date.split('-')
        if len(date_parts) != 3:
            return 'regular'
            
        year, month, day = date_parts
        month = int(month)
        day = int(day)
        
        # Only categorize January/February games
        if month == 1:
            if 13 <= day <= 16:
                return 'wildcard'
            elif 20 <= day <= 22:
                return 'divisional'
            elif 28 <= day <= 31:
                return 'conference'
        elif month == 2:
            if 8 <= day <= 15:
                return 'superbowl'
                
        return 'regular'
        
    except Exception as e:
        logger.error(f"Error categorizing date {game_date}: {e}")
        return 'regular'


def fix_playoff_categorization():
    """Fix playoff game categorization for 2022 and 2023 seasons"""
    logger.info("Starting playoff categorization fix...")
    
    db = SessionLocal()
    try:
        # Get games that might be playoffs (January/February dates)
        jan_games = db.query(Game).filter(
            Game.game_datetime.like('%-01-%')
        ).all()
        
        feb_games = db.query(Game).filter(
            Game.game_datetime.like('%-02-%')
        ).all()
        
        potential_playoffs = jan_games + feb_games
        
        updated_count = 0
        categorization_summary = {
            'wildcard': 0,
            'divisional': 0, 
            'conference': 0,
            'superbowl': 0
        }
        
        for game in potential_playoffs:
            if not game.game_datetime:
                continue
                
            # Only fix games that aren't already categorized
            current_type = game.game_type or 'regular'
            if current_type != 'regular':
                continue
                
            # Determine correct playoff type
            new_type = categorize_playoff_game(game.game_datetime)
            
            if new_type != 'regular':
                logger.info(f"Categorizing {game.game_uid} ({game.game_datetime}) as {new_type}")
                game.game_type = new_type
                categorization_summary[new_type] += 1
                updated_count += 1
        
        # Commit changes
        db.commit()
        
        logger.info("=" * 50)
        logger.info("PLAYOFF CATEGORIZATION COMPLETE")
        logger.info("=" * 50)
        logger.info(f"Total games updated: {updated_count}")
        logger.info(f"Wild Card games: {categorization_summary['wildcard']}")
        logger.info(f"Divisional games: {categorization_summary['divisional']}")
        logger.info(f"Conference games: {categorization_summary['conference']}")
        logger.info(f"Super Bowl games: {categorization_summary['superbowl']}")
        
        return categorization_summary
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to fix categorization: {e}")
        raise
    finally:
        db.close()


def verify_categorization():
    """Verify the categorization results"""
    logger.info("Verifying categorization results...")
    
    db = SessionLocal()
    try:
        for season in [2022, 2023, 2024]:
            games = db.query(Game).filter(Game.season == season).all()
            
            game_types = {}
            for game in games:
                game_type = game.game_type or 'regular'
                game_types[game_type] = game_types.get(game_type, 0) + 1
            
            playoff_count = sum(game_types.get(t, 0) for t in ['wildcard', 'divisional', 'conference', 'superbowl'])
            
            logger.info(f"Season {season}:")
            logger.info(f"  - Total games: {len(games)}")
            logger.info(f"  - Regular season: {game_types.get('regular', 0)}")
            logger.info(f"  - Playoff games: {playoff_count}")
            for ptype in ['wildcard', 'divisional', 'conference', 'superbowl']:
                if game_types.get(ptype, 0) > 0:
                    logger.info(f"    - {ptype}: {game_types[ptype]}")
                    
    finally:
        db.close()


def main():
    """Main execution"""
    logger.info("NFL Playoff Categorization Fix")
    logger.info("=" * 40)
    
    try:
        # Fix categorization
        results = fix_playoff_categorization()
        
        # Verify results
        verify_categorization()
        
        logger.info("=" * 50)
        logger.info("Playoff categorization completed successfully!")
        logger.info("Run test_unified_system.py to verify the results")
        
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise


if __name__ == "__main__":
    main()