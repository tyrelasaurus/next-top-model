#!/usr/bin/env python3
"""
Fix playoff game categorization in CSV data files
Direct CSV processing to fix the categorization issue
"""

import pandas as pd
import logging
from pathlib import Path

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
        year, month, day = game_date.split('-')
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


def fix_csv_playoff_categorization():
    """Fix playoff categorization in CSV files"""
    logger.info("Starting CSV playoff categorization fix...")
    
    data_dir = Path("data")
    csv_files = [
        "nfl_games_2022.csv",
        "nfl_games_2023.csv", 
        "nfl_games_2024.csv",
        "nfl_games_complete.csv",
        "nfl_results.csv"
    ]
    
    total_updated = 0
    
    for csv_file in csv_files:
        file_path = data_dir / csv_file
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            continue
            
        logger.info(f"Processing {csv_file}...")
        
        # Read the CSV
        df = pd.read_csv(file_path)
        logger.info(f"  - Loaded {len(df)} games")
        
        # Fix categorization
        updated_count = 0
        for idx, row in df.iterrows():
            game_date = row.get('date', '')
            current_type = row.get('game_type', '')
            week = row.get('week', '')
            
            # Check if this is a potential playoff game (empty week AND Jan/Feb date)
            is_potential_playoff = (pd.isna(week) or week == '' or week == 'nan') and game_date
            
            # Also check if game_type is empty, nan, or 'regular'
            needs_categorization = (pd.isna(current_type) or current_type == '' or current_type == 'regular' or current_type == 'nan')
            
            if is_potential_playoff and needs_categorization and game_date:
                new_type = categorize_playoff_game(game_date)
                if new_type != 'regular':
                    df.at[idx, 'game_type'] = new_type
                    updated_count += 1
                    logger.info(f"    - {row['game_id']} ({game_date}) -> {new_type}")
        
        # Save the updated CSV
        if updated_count > 0:
            df.to_csv(file_path, index=False)
            logger.info(f"  - Updated {updated_count} games in {csv_file}")
            total_updated += updated_count
        else:
            logger.info(f"  - No changes needed in {csv_file}")
    
    logger.info("=" * 50)
    logger.info("CSV PLAYOFF CATEGORIZATION COMPLETE")
    logger.info("=" * 50)
    logger.info(f"Total games updated: {total_updated}")
    
    return total_updated


def verify_csv_categorization():
    """Verify the categorization results in CSV files"""
    logger.info("Verifying CSV categorization results...")
    
    data_dir = Path("data")
    
    # Check the complete file
    complete_file = data_dir / "nfl_games_complete.csv"
    if complete_file.exists():
        df = pd.read_csv(complete_file)
        
        # Group by season and game type
        summary = df.groupby(['season', 'game_type']).size().unstack(fill_value=0)
        
        logger.info("Game categorization by season:")
        logger.info("\n" + str(summary))
        
        # Check playoff counts
        for season in [2022, 2023, 2024]:
            season_games = df[df['season'] == season]
            playoff_games = season_games[season_games['game_type'].isin(['wildcard', 'divisional', 'conference', 'superbowl'])]
            regular_games = season_games[season_games['game_type'] == 'regular']
            
            logger.info(f"\nSeason {season}:")
            logger.info(f"  - Total games: {len(season_games)}")
            logger.info(f"  - Regular season: {len(regular_games)}")
            logger.info(f"  - Playoff games: {len(playoff_games)}")
            
            if len(playoff_games) > 0:
                playoff_breakdown = playoff_games['game_type'].value_counts()
                for ptype, count in playoff_breakdown.items():
                    logger.info(f"    - {ptype}: {count}")


def main():
    """Main execution"""
    logger.info("NFL CSV Playoff Categorization Fix")
    logger.info("=" * 40)
    
    try:
        # Fix categorization
        updated_count = fix_csv_playoff_categorization()
        
        # Verify results
        verify_csv_categorization()
        
        logger.info("=" * 50)
        logger.info("CSV playoff categorization completed successfully!")
        
        if updated_count > 0:
            logger.info("Re-run export_data.py to update other data files")
        
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise


if __name__ == "__main__":
    main()