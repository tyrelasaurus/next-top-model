#!/bin/bash

# Autonomous ESPN Statistics Collector
# Run this in a separate terminal - it will work independently
# Will automatically restart until all data is collected

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
source venv/bin/activate

# Create log file with timestamp
LOG_FILE="autonomous_collection_$(date +%Y%m%d_%H%M%S).log"

echo "=====================================================================" | tee -a "$LOG_FILE"
echo "AUTONOMOUS ESPN STATISTICS COLLECTOR STARTED" | tee -a "$LOG_FILE"
echo "=====================================================================" | tee -a "$LOG_FILE"
echo "Started at: $(date)" | tee -a "$LOG_FILE"
echo "Working directory: $SCRIPT_DIR" | tee -a "$LOG_FILE"
echo "Log file: $LOG_FILE" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

restart_count=0
max_restarts=200

while [ $restart_count -lt $max_restarts ]; do
    restart_count=$((restart_count + 1))
    
    echo "=== COLLECTION RUN #$restart_count ===" | tee -a "$LOG_FILE"
    echo "Started at: $(date)" | tee -a "$LOG_FILE"
    
    # Run the collector
    python espn_overnight_stats_collector.py 2>&1 | tee -a "$LOG_FILE"
    exit_code=$?
    
    echo "Collector exited with code: $exit_code at $(date)" | tee -a "$LOG_FILE"
    
    # Check if collection completed successfully
    if [ $exit_code -eq 0 ]; then
        echo "🎯 COLLECTION COMPLETED SUCCESSFULLY!" | tee -a "$LOG_FILE"
        echo "All data has been gathered at $(date)" | tee -a "$LOG_FILE"
        break
    fi
    
    # Check current progress
    echo "Checking collection progress..." | tee -a "$LOG_FILE"
    python -c "
import sys
sys.path.append('.')
try:
    from app.core.database import SessionLocal
    from app.models.sports import Game, TeamGameStat, TeamSeasonStat
    
    with SessionLocal() as db:
        total_games = db.query(Game).filter(Game.season >= 2022).count()
        team_game_stats = db.query(TeamGameStat).count()
        team_season_stats = db.query(TeamSeasonStat).count()
        
        games_with_stats = team_game_stats // 2  # 2 stats per game
        coverage = (games_with_stats / total_games * 100) if total_games > 0 else 0
        
        print(f'Progress: {games_with_stats}/{total_games} games ({coverage:.1f}% coverage)')
        print(f'Team game stats: {team_game_stats} records')
        print(f'Team season stats: {team_season_stats} records')
        
        # Check if we're essentially done (95%+ coverage)
        if coverage >= 95.0 and team_season_stats >= 90:
            print('COLLECTION APPEARS COMPLETE!')
            exit(0)
        else:
            print('Collection continuing...')
            exit(1)
            
except Exception as e:
    print(f'Error checking progress: {e}')
    exit(1)
" 2>&1 | tee -a "$LOG_FILE"
    
    progress_check=$?
    
    if [ $progress_check -eq 0 ]; then
        echo "🎯 COLLECTION APPEARS COMPLETE!" | tee -a "$LOG_FILE"
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
echo "=====================================================================" | tee -a "$LOG_FILE"
echo "AUTONOMOUS COLLECTOR FINISHED" | tee -a "$LOG_FILE"
echo "=====================================================================" | tee -a "$LOG_FILE"
echo "Finished at: $(date)" | tee -a "$LOG_FILE"
echo "Total restart attempts: $restart_count" | tee -a "$LOG_FILE"

# Final status check
echo "FINAL STATUS:" | tee -a "$LOG_FILE"
python -c "
import sys
sys.path.append('.')
try:
    from app.core.database import SessionLocal
    from app.models.sports import Game, TeamGameStat, TeamSeasonStat
    
    with SessionLocal() as db:
        total_games = db.query(Game).filter(Game.season >= 2022).count()
        team_game_stats = db.query(TeamGameStat).count()
        team_season_stats = db.query(TeamSeasonStat).count()
        
        games_with_stats = team_game_stats // 2
        coverage = (games_with_stats / total_games * 100) if total_games > 0 else 0
        
        print(f'Final Coverage: {games_with_stats}/{total_games} games ({coverage:.1f}%)')
        print(f'Team Game Stats: {team_game_stats} records')
        print(f'Team Season Stats: {team_season_stats} records')
        
except Exception as e:
    print(f'Error in final status: {e}')
" 2>&1 | tee -a "$LOG_FILE"

echo "Log saved to: $LOG_FILE" | tee -a "$LOG_FILE"