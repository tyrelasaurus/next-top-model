#!/usr/bin/env python3
"""
Alternative Data Sources Strategy for NFL Granular Data
Research and implement fallback scrapers for free data sources
"""

import asyncio
import logging
import sys
import requests
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.models.sports import Game, Team

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DataSource:
    name: str
    url_pattern: str
    data_types: List[str]
    rate_limit: float
    reliability: str
    notes: str

class AlternativeDataSources:
    """Research and implement alternative NFL data sources"""
    
    def __init__(self):
        self.sources = self.define_data_sources()
    
    def define_data_sources(self) -> List[DataSource]:
        """Define available free NFL data sources"""
        
        return [
            # ESPN - Free, comprehensive
            DataSource(
                name="ESPN NFL",
                url_pattern="https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
                data_types=["scores", "attendance", "weather", "venue"],
                rate_limit=2.0,
                reliability="High",
                notes="Free API, good for recent games, includes weather and attendance"
            ),
            
            # NFL.com - Official but limited
            DataSource(
                name="NFL.com Official",
                url_pattern="https://www.nfl.com/schedules/",
                data_types=["scores", "venue", "attendance"],
                rate_limit=3.0,
                reliability="High",
                notes="Official source, good data quality, limited historical"
            ),
            
            # Sports Reference (alternative to PFR)
            DataSource(
                name="Sports Reference Alternative",
                url_pattern="https://www.sports-reference.com/cfb/",
                data_types=["detailed_stats", "weather", "attendance"],
                rate_limit=5.0,
                reliability="Medium",
                notes="Different Sports Reference property, may have less traffic"
            ),
            
            # Wikipedia - Surprisingly detailed for major games
            DataSource(
                name="Wikipedia NFL",
                url_pattern="https://en.wikipedia.org/wiki/",
                data_types=["attendance", "venue", "notable_events"],
                rate_limit=1.0,
                reliability="Medium",
                notes="Good for playoff games and notable matchups"
            ),
            
            # Weather APIs for historical data
            DataSource(
                name="OpenWeatherMap Historical",
                url_pattern="http://api.openweathermap.org/data/2.5/onecall/timemachine",
                data_types=["weather"],
                rate_limit=1.0,
                reliability="High",
                notes="Free tier: 60 calls/min, requires API key but free tier available"
            ),
            
            # FiveThirtyEight - Analytics focused
            DataSource(
                name="FiveThirtyEight NFL",
                url_pattern="https://projects.fivethirtyeight.com/",
                data_types=["analytics", "predictions"],
                rate_limit=2.0,
                reliability="Medium",
                notes="Analytics and predictions, limited raw game data"
            ),
            
            # Reddit NFL - Community data
            DataSource(
                name="Reddit NFL Data",
                url_pattern="https://www.reddit.com/r/nfl/",
                data_types=["community_stats", "game_threads"],
                rate_limit=1.0,
                reliability="Low",
                notes="Community-driven, good for context and unofficial stats"
            ),
            
            # Sportradar (has free tier)
            DataSource(
                name="Sportradar Free Tier",
                url_pattern="https://developer.sportradar.com/",
                data_types=["comprehensive"],
                rate_limit=1.0,
                reliability="High",
                notes="Limited free tier, very comprehensive when available"
            )
        ]
    
    async def test_espn_api(self) -> Dict:
        """Test ESPN's free NFL API"""
        logger.info("Testing ESPN NFL API...")
        
        try:
            # Test current week
            url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            games = data.get('events', [])
            sample_game = games[0] if games else None
            
            available_data = []
            if sample_game:
                competition = sample_game.get('competitions', [{}])[0]
                
                if competition.get('attendance'):
                    available_data.append("attendance")
                
                if competition.get('weather'):
                    available_data.append("weather")
                
                if competition.get('venue'):
                    available_data.append("venue")
                
                if sample_game.get('status'):
                    available_data.append("game_status")
            
            return {
                "source": "ESPN",
                "status": "success",
                "games_found": len(games),
                "available_data": available_data,
                "sample_structure": sample_game.keys() if sample_game else []
            }
            
        except Exception as e:
            return {
                "source": "ESPN",
                "status": "error",
                "error": str(e)
            }
    
    async def test_historical_weather_approach(self, sample_game: Game) -> Dict:
        """Test getting historical weather for a game using GPS coordinates"""
        
        if not sample_game.game_datetime:
            return {"status": "error", "error": "No game datetime"}
        
        # Get stadium coordinates
        with SessionLocal() as db:
            home_team = db.query(Team).filter(Team.team_uid == sample_game.home_team_uid).first()
            
            if not home_team or not home_team.latitude:
                return {"status": "error", "error": "No stadium coordinates"}
        
        # Mock weather API call (would need API key for real implementation)
        logger.info(f"Would query weather for {home_team.stadium_name} on {sample_game.game_datetime}")
        logger.info(f"Coordinates: {home_team.latitude}, {home_team.longitude}")
        
        return {
            "status": "feasible",
            "approach": "historical_weather_api",
            "coordinates": f"{home_team.latitude}, {home_team.longitude}",
            "date": sample_game.game_datetime.isoformat(),
            "stadium": home_team.stadium_name
        }
    
    async def test_wikipedia_scraping(self, season: int) -> Dict:
        """Test Wikipedia scraping for major games"""
        logger.info(f"Testing Wikipedia scraping for {season} season...")
        
        try:
            # Test Super Bowl page
            url = f"https://en.wikipedia.org/wiki/{season}_NFL_season"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            content = response.text
            
            # Look for attendance patterns
            attendance_found = "attendance" in content.lower()
            weather_found = any(term in content.lower() for term in ["temperature", "weather", "°f", "°c"])
            
            return {
                "source": "Wikipedia",
                "status": "success",
                "url": url,
                "attendance_data": attendance_found,
                "weather_data": weather_found,
                "content_length": len(content)
            }
            
        except Exception as e:
            return {
                "source": "Wikipedia",
                "status": "error",
                "error": str(e)
            }
    
    async def create_scraping_priority_strategy(self) -> Dict:
        """Create a prioritized scraping strategy based on data needs"""
        
        # Analyze current data gaps
        with SessionLocal() as db:
            total_games = db.query(Game).count()
            playoff_games = db.query(Game).filter(
                Game.game_type.in_(['wildcard', 'divisional', 'conference', 'superbowl'])
            ).count()
            recent_games = db.query(Game).filter(Game.season >= 2023).count()
            
        strategy = {
            "data_priorities": [
                {
                    "priority": 1,
                    "data_type": "attendance",
                    "rationale": "Most reliable and available across sources",
                    "recommended_sources": ["ESPN", "NFL.com", "Wikipedia for playoffs"],
                    "games_to_target": f"{playoff_games} playoff games first"
                },
                {
                    "priority": 2,
                    "data_type": "weather", 
                    "rationale": "Available through multiple approaches",
                    "recommended_sources": ["Historical Weather APIs", "PFR selective", "Wikipedia"],
                    "games_to_target": "Outdoor stadiums, cold weather games"
                },
                {
                    "priority": 3,
                    "data_type": "detailed_stats",
                    "rationale": "Lower priority, most complex to obtain",
                    "recommended_sources": ["PFR selective", "ESPN for recent"],
                    "games_to_target": "Playoff games and notable matchups"
                }
            ],
            
            "phased_approach": [
                {
                    "phase": 1,
                    "description": "ESPN API Integration",
                    "target": "Recent games (2023-2024)",
                    "expected_coverage": f"{recent_games} games",
                    "effort": "Low",
                    "success_rate": "High"
                },
                {
                    "phase": 2, 
                    "description": "Historical Weather Augmentation",
                    "target": "Outdoor stadiums all seasons",
                    "expected_coverage": "~800 outdoor games",
                    "effort": "Medium",
                    "success_rate": "High"
                },
                {
                    "phase": 3,
                    "description": "Selective PFR + Wikipedia",
                    "target": "Playoff games and major matchups",
                    "expected_coverage": f"{playoff_games} playoff games",
                    "effort": "Medium",
                    "success_rate": "Medium"
                },
                {
                    "phase": 4,
                    "description": "Community Data Integration",
                    "target": "Reddit/Community stats for context",
                    "expected_coverage": "Metadata and context",
                    "effort": "Low",
                    "success_rate": "Low"
                }
            ],
            
            "rate_limiting_strategy": {
                "conservative": "3-5 seconds between requests",
                "aggressive": "1-2 seconds between requests", 
                "burst": "Multiple sources in parallel",
                "recommendation": "Conservative with burst for different sources"
            }
        }
        
        return strategy

async def main():
    """Main execution - test alternative data sources"""
    logger.info("=" * 80)
    logger.info("ALTERNATIVE NFL DATA SOURCES ANALYSIS")
    logger.info("=" * 80)
    
    sources = AlternativeDataSources()
    
    # Test ESPN API
    espn_test = await sources.test_espn_api()
    logger.info(f"\nESPN API Test: {espn_test}")
    
    # Test weather approach
    with SessionLocal() as db:
        sample_game = db.query(Game).filter(Game.game_datetime.isnot(None)).first()
        if sample_game:
            weather_test = await sources.test_historical_weather_approach(sample_game)
            logger.info(f"\nWeather API Test: {weather_test}")
    
    # Test Wikipedia
    wiki_test = await sources.test_wikipedia_scraping(2024)
    logger.info(f"\nWikipedia Test: {wiki_test}")
    
    # Create strategy
    strategy = await sources.create_scraping_priority_strategy()
    
    logger.info("\n" + "=" * 60)
    logger.info("RECOMMENDED STRATEGY")
    logger.info("=" * 60)
    
    logger.info("\nData Priorities:")
    for priority in strategy["data_priorities"]:
        logger.info(f"{priority['priority']}. {priority['data_type']}: {priority['rationale']}")
        logger.info(f"   Sources: {', '.join(priority['recommended_sources'])}")
        logger.info(f"   Target: {priority['games_to_target']}")
    
    logger.info("\nPhased Implementation:")
    for phase in strategy["phased_approach"]:
        logger.info(f"Phase {phase['phase']}: {phase['description']}")
        logger.info(f"   Target: {phase['target']} ({phase['expected_coverage']})")
        logger.info(f"   Effort: {phase['effort']}, Success Rate: {phase['success_rate']}")
    
    logger.info(f"\nRate Limiting: {strategy['rate_limiting_strategy']['recommendation']}")
    
    logger.info("\n" + "=" * 60)
    logger.info("NEXT STEPS RECOMMENDATIONS")
    logger.info("=" * 60)
    logger.info("1. Implement ESPN API scraper for recent games (high success rate)")
    logger.info("2. Add historical weather API integration for outdoor stadiums")
    logger.info("3. Create selective PFR scraper focusing only on playoff games")
    logger.info("4. Use Wikipedia for Super Bowl and major game details")
    logger.info("5. Implement parallel scraping with different sources")

if __name__ == "__main__":
    asyncio.run(main())