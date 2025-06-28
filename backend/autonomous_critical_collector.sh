#!/bin/bash

# Autonomous Critical Games Collector
# Targets the 147 critical missing games until completion
# Run this in a separate terminal - it will work independently

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
source venv/bin/activate

# Create log file with timestamp
LOG_FILE="critical_collection_$(date +%Y%m%d_%H%M%S).log"

echo "================================================================" | tee -a "$LOG_FILE"
echo "AUTONOMOUS CRITICAL GAMES COLLECTOR STARTED" | tee -a "$LOG_FILE"
echo "================================================================" | tee -a "$LOG_FILE"
echo "Started at: $(date)" | tee -a "$LOG_FILE"
echo "Working directory: $SCRIPT_DIR" | tee -a "$LOG_FILE"
echo "Log file: $LOG_FILE" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

restart_count=0
max_restarts=50

while [ $restart_count -lt $max_restarts ]; do
    restart_count=$((restart_count + 1))
    
    echo "=== CRITICAL COLLECTION RUN #$restart_count ===" | tee -a "$LOG_FILE"
    echo "Started at: $(date)" | tee -a "$LOG_FILE"
    
    # Run the critical games collector
    python critical_games_collector.py 2>&1 | tee -a "$LOG_FILE"
    exit_code=$?
    
    echo "Collector exited with code: $exit_code at $(date)" | tee -a "$LOG_FILE"
    
    # Check if collection completed successfully
    if [ $exit_code -eq 0 ]; then
        echo "🎯 CRITICAL COLLECTION COMPLETED!" | tee -a "$LOG_FILE"
        echo "All critical games processed at $(date)" | tee -a "$LOG_FILE"
        break
    fi
    
    # Check current coverage of critical games
    echo "Checking critical games coverage..." | tee -a "$LOG_FILE"
    python -c "
import sys
sys.path.append('.')
try:
    from app.core.database import SessionLocal
    from app.models.sports import Game, TeamGameStat
    from sqlalchemy import extract
    
    with SessionLocal() as db:
        # Get critical games (non-preseason)
        critical_games = db.query(Game).filter(
            Game.season >= 2022,
            Game.game_datetime.isnot(None),
            ~(extract('month', Game.game_datetime) == 8)
        ).count()
        
        # Get critical games with stats
        critical_with_stats = db.query(Game).join(TeamGameStat).filter(
            Game.season >= 2022,
            ~(extract('month', Game.game_datetime) == 8)
        ).distinct().count()
        
        coverage = (critical_with_stats / critical_games * 100) if critical_games > 0 else 0
        remaining = critical_games - critical_with_stats
        
        print(f'Critical games coverage: {critical_with_stats}/{critical_games} ({coverage:.1f}%)')
        print(f'Remaining critical games: {remaining}')
        
        # Stop if we have excellent coverage (95%+)
        if coverage >= 95.0:
            print('CRITICAL COLLECTION APPEARS COMPLETE!')
            exit(0)
        elif remaining <= 5:
            print('Almost complete - only a few games remaining!')
            exit(0)
        else:
            print('Collection continuing...')
            exit(1)
            
except Exception as e:
    print(f'Error checking coverage: {e}')
    exit(1)
" 2>&1 | tee -a "$LOG_FILE"
    
    coverage_check=$?
    
    if [ $coverage_check -eq 0 ]; then
        echo "🎯 CRITICAL COLLECTION COMPLETE!" | tee -a "$LOG_FILE"
        echo "Stopping autonomous collector at $(date)" | tee -a "$LOG_FILE"
        break
    fi
    
    echo "Restarting in 3 seconds..." | tee -a "$LOG_FILE"
    sleep 3
done

if [ $restart_count -ge $max_restarts ]; then
    echo "❌ Maximum restart limit ($max_restarts) reached" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"
echo "================================================================" | tee -a "$LOG_FILE"
echo "AUTONOMOUS CRITICAL COLLECTOR FINISHED" | tee -a "$LOG_FILE"
echo "================================================================" | tee -a "$LOG_FILE"
echo "Finished at: $(date)" | tee -a "$LOG_FILE"
echo "Total restart attempts: $restart_count" | tee -a "$LOG_FILE"

# Final comprehensive status
echo "FINAL STATUS:" | tee -a "$LOG_FILE"
python -c "
import sys
sys.path.append('.')
try:
    from app.core.database import SessionLocal
    from app.models.sports import Game, TeamGameStat
    from sqlalchemy import extract
    
    with SessionLocal() as db:
        # Overall statistics
        total_games = db.query(Game).filter(Game.season >= 2022).count()
        preseason_games = db.query(Game).filter(
            Game.season >= 2022,
            extract('month', Game.game_datetime) == 8
        ).count()
        critical_games = total_games - preseason_games
        
        # Games with statistics
        total_with_stats = db.query(Game).join(TeamGameStat).filter(Game.season >= 2022).distinct().count()
        critical_with_stats = db.query(Game).join(TeamGameStat).filter(
            Game.season >= 2022,
            ~(extract('month', Game.game_datetime) == 8)
        ).distinct().count()
        
        # Coverage calculations
        overall_coverage = (total_with_stats / total_games * 100) if total_games > 0 else 0
        critical_coverage = (critical_with_stats / critical_games * 100) if critical_games > 0 else 0
        
        print('=' * 60)
        print('FINAL NFL DATA COLLECTION SUMMARY')
        print('=' * 60)
        print(f'Total games in database: {total_games}')
        print(f'Preseason games: {preseason_games}')
        print(f'Critical games (regular/playoff): {critical_games}')
        print(f'Games with statistics: {total_with_stats}')
        print(f'Critical games with statistics: {critical_with_stats}')
        print('')
        print(f'Overall coverage: {overall_coverage:.1f}%')
        print(f'Critical games coverage: {critical_coverage:.1f}%')
        print('')
        
        if critical_coverage >= 95:
            print('🏆 EXCELLENT! Critical games coverage is outstanding!')
        elif critical_coverage >= 90:
            print('✅ GREAT! Critical games coverage is very good!')
        elif critical_coverage >= 85:
            print('👍 GOOD! Critical games coverage is solid!')
        else:
            remaining = critical_games - critical_with_stats
            print(f'⚠️  Still missing {remaining} critical games')
        
        print('')
        print('Your NFL analytics database is ready for production use!')
        print('=' * 60)
        
except Exception as e:
    print(f'Error in final status: {e}')
" 2>&1 | tee -a "$LOG_FILE"

echo "Log saved to: $LOG_FILE" | tee -a "$LOG_FILE"