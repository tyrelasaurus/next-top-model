#!/usr/bin/env python3
"""
Auto-Restart Wrapper for ESPN Stats Collector
Automatically restarts the collector after timeouts until all data is gathered
"""

import subprocess
import sys
import time
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - AUTO-RESTART - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("auto_restart_collector.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_collector():
    """Run the ESPN stats collector with automatic restart"""
    restart_count = 0
    max_restarts = 100  # Safety limit
    
    logger.info("=" * 80)
    logger.info("AUTO-RESTART ESPN STATISTICS COLLECTOR")
    logger.info("=" * 80)
    logger.info("Will automatically restart collector after timeouts until completion")
    
    while restart_count < max_restarts:
        try:
            logger.info(f"Starting collection run #{restart_count + 1}")
            
            # Run the collector
            result = subprocess.run([
                sys.executable, 
                "espn_overnight_stats_collector.py"
            ], 
            cwd=Path(__file__).parent,
            capture_output=False,  # Let output stream through
            timeout=None  # No timeout - let it run
            )
            
            if result.returncode == 0:
                logger.info("🎯 COLLECTION COMPLETED SUCCESSFULLY!")
                logger.info("All data has been gathered.")
                break
            else:
                logger.warning(f"Collector exited with code {result.returncode}")
                restart_count += 1
                
        except subprocess.TimeoutExpired:
            logger.info("⏰ Collector timed out - restarting automatically...")
            restart_count += 1
            time.sleep(2)  # Brief pause before restart
            
        except KeyboardInterrupt:
            logger.info("🛑 Manual interruption - stopping auto-restart")
            break
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            restart_count += 1
            time.sleep(5)  # Longer pause on errors
    
    if restart_count >= max_restarts:
        logger.error(f"❌ Maximum restart limit ({max_restarts}) reached")
        return 1
    
    logger.info("✅ Auto-restart collector finished")
    return 0

if __name__ == "__main__":
    exit_code = run_collector()
    sys.exit(exit_code)