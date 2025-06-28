#!/usr/bin/env python3
"""
Comprehensive Game Categorization System
Properly categorizes preseason, regular season, and playoff games based on multiple criteria
"""

import pandas as pd
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def categorize_game_comprehensive(game_date: str, week: str, season: int) -> str:
    """
    Comprehensive game categorization based on date, week, and season context
    
    NFL Schedule patterns:
    - Preseason: August - Early September (weeks 0 or negative, before regular season starts)
    - Regular Season: September - January (weeks 1-18)
    - Playoffs: January - February (Wild Card, Divisional, Conference, Super Bowl)
    
    Args:
        game_date: Date in YYYY-MM-DD format
        week: Week number (can be empty, float, or string)
        season: NFL season year
    """
    try:
        # Parse date
        date_obj = datetime.strptime(game_date, '%Y-%m-%d')
        month = date_obj.month
        day = date_obj.day
        
        # Parse week (handle various formats)
        week_num = None
        if pd.notna(week) and str(week).strip() != '' and str(week) != 'nan':
            try:
                week_num = float(week)
            except (ValueError, TypeError):
                pass
        
        # Preseason detection
        if month == 8:  # August is always preseason
            return 'preseason'
        elif month == 9 and day <= 10:  # Early September might be preseason
            if week_num is None or week_num <= 0:
                return 'preseason'
        
        # Regular season detection
        if week_num is not None and 1 <= week_num <= 18:
            return 'regular'
        
        # Playoff detection (empty week + Jan/Feb dates)
        if week_num is None or week_num == '' or pd.isna(week_num):
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
        
        # Default to regular season for September-December games
        if 9 <= month <= 12:
            return 'regular'
        elif month == 1 and day <= 8:  # Early January regular season (Week 18)
            return 'regular'
            
        # If we can't determine, return original or regular
        return 'regular'
        
    except Exception as e:
        logger.error(f"Error categorizing date {game_date}, week {week}: {e}")
        return 'regular'


def analyze_all_game_types():
    """Analyze and categorize all games in the dataset"""
    logger.info("Starting comprehensive game type analysis...")
    
    data_file = Path("data/nfl_games_complete.csv")
    if not data_file.exists():
        logger.error(f"Data file not found: {data_file}")
        return
    
    # Load data
    df = pd.read_csv(data_file)
    logger.info(f"Loaded {len(df)} total games")
    
    # Analyze current categorization
    logger.info("\nCurrent game type distribution:")
    current_types = df['game_type'].value_counts()
    for game_type, count in current_types.items():
        logger.info(f"  {game_type}: {count}")
    
    # Analyze games by date patterns
    logger.info("\nAnalyzing by date patterns:")
    
    # Check for potential preseason games
    df['date_obj'] = pd.to_datetime(df['date'])
    df['month'] = df['date_obj'].dt.month
    df['day'] = df['date_obj'].dt.day
    
    # August games
    august_games = df[df['month'] == 8]
    logger.info(f"August games: {len(august_games)} (likely preseason)")
    
    # Early September games
    early_sept_games = df[(df['month'] == 9) & (df['day'] <= 10)]
    logger.info(f"Early September games (1-10): {len(early_sept_games)} (check for preseason)")
    
    # Games with empty weeks
    empty_week_games = df[df['week'].isna() | (df['week'] == '') | (df['week'] == 'nan')]
    logger.info(f"Games with empty weeks: {len(empty_week_games)}")
    
    # Show date range for empty week games
    if len(empty_week_games) > 0:
        empty_week_dates = empty_week_games['date'].unique()
        logger.info(f"Empty week game date range: {min(empty_week_dates)} to {max(empty_week_dates)}")
    
    # Analyze by season
    logger.info("\nAnalysis by season:")
    for season in sorted(df['season'].unique()):
        season_games = df[df['season'] == season]
        logger.info(f"\nSeason {season}: {len(season_games)} games")
        
        # Break down by month
        monthly_breakdown = season_games.groupby('month').size()
        for month, count in monthly_breakdown.items():
            month_names = {8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec', 1: 'Jan', 2: 'Feb'}
            logger.info(f"  {month_names.get(month, month)}: {count} games")
        
        # Check for specific patterns
        season_empty_week = season_games[season_games['week'].isna() | (season_games['week'] == '')]
        if len(season_empty_week) > 0:
            logger.info(f"  Empty week games: {len(season_empty_week)}")
            for _, game in season_empty_week.iterrows():
                logger.info(f"    {game['game_id']}: {game['date']} ({game.get('game_type', 'N/A')})")


def fix_comprehensive_categorization():
    """Apply comprehensive categorization to all games"""
    logger.info("Applying comprehensive game categorization...")
    
    data_file = Path("data/nfl_games_complete.csv")
    df = pd.read_csv(data_file)
    
    updated_count = 0
    categorization_changes = {}
    
    for idx, row in df.iterrows():
        current_type = row.get('game_type', '')
        game_date = row.get('date', '')
        week = row.get('week', '')
        season = row.get('season', 0)
        
        if game_date:
            new_type = categorize_game_comprehensive(game_date, week, season)
            
            # Only update if different from current
            if new_type != current_type:
                old_type = current_type if current_type else 'empty'
                logger.info(f"  {row['game_id']} ({game_date}): {old_type} -> {new_type}")
                
                df.at[idx, 'game_type'] = new_type
                updated_count += 1
                
                # Track changes
                change_key = f"{old_type} -> {new_type}"
                categorization_changes[change_key] = categorization_changes.get(change_key, 0) + 1
    
    # Save updated data
    if updated_count > 0:
        df.to_csv(data_file, index=False)
        logger.info(f"\nUpdated {updated_count} games")
        
        logger.info("Categorization changes:")
        for change, count in categorization_changes.items():
            logger.info(f"  {change}: {count} games")
    else:
        logger.info("No changes needed")
    
    # Show final distribution
    logger.info("\nFinal game type distribution:")
    final_types = df['game_type'].value_counts()
    for game_type, count in final_types.items():
        logger.info(f"  {game_type}: {count}")
    
    return updated_count


def verify_categorization_accuracy():
    """Verify the accuracy of game categorization"""
    logger.info("Verifying categorization accuracy...")
    
    data_file = Path("data/nfl_games_complete.csv")
    df = pd.read_csv(data_file)
    
    issues = []
    
    # Convert date to datetime for analysis
    df['date_obj'] = pd.to_datetime(df['date'])
    df['month'] = df['date_obj'].dt.month
    
    for _, row in df.iterrows():
        game_type = row['game_type']
        month = row['month']
        week = row.get('week', '')
        game_id = row['game_id']
        
        # Verify preseason games
        if game_type == 'preseason':
            if month not in [8, 9]:
                issues.append(f"{game_id}: Preseason game not in Aug/Sep ({row['date']})")
        
        # Verify regular season games
        elif game_type == 'regular':
            if month in [8] and pd.notna(week):
                issues.append(f"{game_id}: Regular season game in August ({row['date']})")
            elif month in [2] and row['date_obj'].day > 5:
                issues.append(f"{game_id}: Regular season game in late February ({row['date']})")
        
        # Verify playoff games
        elif game_type in ['wildcard', 'divisional', 'conference', 'superbowl']:
            if month not in [1, 2]:
                issues.append(f"{game_id}: Playoff game not in Jan/Feb ({row['date']})")
    
    logger.info(f"Verification complete. Found {len(issues)} potential issues:")
    for issue in issues[:10]:  # Show first 10 issues
        logger.info(f"  {issue}")
    
    if len(issues) > 10:
        logger.info(f"  ... and {len(issues) - 10} more issues")
    
    return len(issues)


def main():
    """Main execution"""
    logger.info("Comprehensive Game Categorization Analysis")
    logger.info("=" * 60)
    
    try:
        # Step 1: Analyze current state
        analyze_all_game_types()
        
        logger.info("\n" + "=" * 60)
        
        # Step 2: Apply comprehensive categorization
        updated_count = fix_comprehensive_categorization()
        
        logger.info("\n" + "=" * 60)
        
        # Step 3: Verify accuracy
        issues_count = verify_categorization_accuracy()
        
        logger.info("\n" + "=" * 60)
        logger.info("COMPREHENSIVE CATEGORIZATION COMPLETE")
        logger.info(f"Games updated: {updated_count}")
        logger.info(f"Verification issues: {issues_count}")
        
        if updated_count > 0:
            logger.info("Data has been updated. Consider re-running export scripts.")
        
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise


if __name__ == "__main__":
    main()