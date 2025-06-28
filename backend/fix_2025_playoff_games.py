#!/usr/bin/env python3
"""
Fix 2025 playoff games categorization
Properly categorizes 2025 games that are actually 2024 season playoffs
"""

import pandas as pd
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_2025_playoff_categorization():
    """Fix 2025 games that are actually 2024 season playoffs"""
    logger.info("Fixing 2025 playoff game categorization...")
    
    data_file = Path("data/nfl_games_complete.csv")
    df = pd.read_csv(data_file)
    
    # Find 2025 games that should be playoffs
    games_2025 = df[df['date'].str.startswith('2025-')]
    logger.info(f"Found {len(games_2025)} games in 2025")
    
    updated_count = 0
    
    for idx, row in df.iterrows():
        if not row['date'].startswith('2025-'):
            continue
            
        game_date = row['date']
        current_type = row.get('game_type', '')
        week = row.get('week', '')
        
        # Parse date
        month = int(game_date.split('-')[1])
        day = int(game_date.split('-')[2])
        
        new_type = None
        
        # 2025 playoff schedule (2024 season playoffs)
        if month == 1:
            if 11 <= day <= 13:  # Wild Card Weekend
                new_type = 'wildcard'
            elif 18 <= day <= 19:  # Divisional Round
                new_type = 'divisional'
            elif 26 <= day <= 26:  # Conference Championships
                new_type = 'conference'
        elif month == 2:
            if 9 <= day <= 9:  # Super Bowl
                new_type = 'superbowl'
        
        # Only update if we determined a playoff type and it's different
        if new_type and new_type != current_type:
            logger.info(f"  {row['game_id']} ({game_date}): {current_type} -> {new_type}")
            df.at[idx, 'game_type'] = new_type
            
            # Also clear the week field for playoff games
            df.at[idx, 'week'] = ''
            
            updated_count += 1
    
    # Save updated data
    if updated_count > 0:
        df.to_csv(data_file, index=False)
        logger.info(f"Updated {updated_count} games")
        
        # Update other CSV files too
        for csv_file in ["data/nfl_games_2024.csv", "data/nfl_results.csv"]:
            if Path(csv_file).exists():
                df_subset = df[df['season'] == 2024] if '2024' in csv_file else df
                df_subset.to_csv(csv_file, index=False)
                logger.info(f"Updated {csv_file}")
    
    return updated_count


def verify_final_categorization():
    """Verify the final game categorization"""
    logger.info("Verifying final game categorization...")
    
    data_file = Path("data/nfl_games_complete.csv")
    df = pd.read_csv(data_file)
    
    # Overall distribution
    logger.info("Final game type distribution:")
    type_counts = df['game_type'].value_counts()
    for game_type, count in type_counts.items():
        logger.info(f"  {game_type}: {count}")
    
    # By season
    logger.info("\nBreakdown by season:")
    for season in sorted(df['season'].unique()):
        season_games = df[df['season'] == season]
        season_types = season_games['game_type'].value_counts()
        
        regular = season_types.get('regular', 0)
        playoff_types = ['wildcard', 'divisional', 'conference', 'superbowl']
        playoffs = sum(season_types.get(ptype, 0) for ptype in playoff_types)
        
        logger.info(f"\n  Season {season}: {len(season_games)} total games")
        logger.info(f"    Regular season: {regular}")
        logger.info(f"    Playoffs: {playoffs}")
        
        for ptype in playoff_types:
            if season_types.get(ptype, 0) > 0:
                logger.info(f"      {ptype}: {season_types[ptype]}")
    
    # Check for 2025 games
    games_2025 = df[df['date'].str.startswith('2025-')]
    if len(games_2025) > 0:
        logger.info(f"\n2025 games breakdown:")
        type_2025 = games_2025['game_type'].value_counts()
        for game_type, count in type_2025.items():
            logger.info(f"  {game_type}: {count}")


def main():
    """Main execution"""
    logger.info("2025 Playoff Games Categorization Fix")
    logger.info("=" * 50)
    
    try:
        # Fix 2025 playoff categorization
        updated_count = fix_2025_playoff_categorization()
        
        # Verify results
        verify_final_categorization()
        
        logger.info("\n" + "=" * 50)
        logger.info("2025 PLAYOFF CATEGORIZATION COMPLETE")
        logger.info(f"Games updated: {updated_count}")
        
        if updated_count > 0:
            logger.info("Re-run export_data.py to update all data files")
        
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise


if __name__ == "__main__":
    main()