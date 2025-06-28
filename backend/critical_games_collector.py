#!/usr/bin/env python3
"""
Critical Games Collector - Target the 147 legitimate missing games
Uses multiple strategies to find ESPN data for regular season and playoff games
"""

import asyncio
import aiohttp
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json
from sqlalchemy import extract

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.models.sports import Game, TeamGameStat, Team
from team_id_mappings import find_team_by_name_fuzzy, get_nfl_abbr

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class CriticalGamesCollector:
    def __init__(self):
        self.session = None
        self.collected_count = 0
        self.failed_count = 0
        
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=10)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def find_espn_game_multiple_strategies(self, game):
        """Try multiple strategies to find ESPN game ID"""
        
        with SessionLocal() as db:
            home_team = db.query(Team).filter(Team.team_uid == game.home_team_uid).first()
            away_team = db.query(Team).filter(Team.team_uid == game.away_team_uid).first()
            
            if not home_team or not away_team:
                return None
        
        # Strategy 1: Standard ESPN API format
        game_date = game.game_datetime.strftime("%Y%m%d")
        standard_url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={game_date}"
        
        espn_id = await self._try_espn_url(standard_url, home_team, away_team, game.game_datetime)
        if espn_id:
            return espn_id
        
        # Strategy 2: Try with team abbreviations
        if home_team.abbreviation and away_team.abbreviation:
            teams_url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{home_team.abbreviation.lower()}/schedule?season={game.season}"
            espn_id = await self._try_team_schedule(teams_url, away_team, game.game_datetime)
            if espn_id:
                return espn_id
        
        # Strategy 3: Try week-based search
        if game.week:
            week = int(game.week) if game.week == int(game.week) else int(game.week) + 1
            week_url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?seasontype=2&week={week}&year={game.season}"
            espn_id = await self._try_espn_url(week_url, home_team, away_team, game.game_datetime)
            if espn_id:
                return espn_id
        
        # Strategy 4: Try broader date range
        for days_offset in [-1, 1, -2, 2]:
            alt_date = game.game_datetime + timedelta(days=days_offset)
            alt_date_str = alt_date.strftime("%Y%m%d")
            alt_url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={alt_date_str}"
            
            espn_id = await self._try_espn_url(alt_url, home_team, away_team, game.game_datetime)
            if espn_id:
                return espn_id
        
        return None
    
    async def _try_espn_url(self, url, home_team, away_team, target_datetime):
        """Try to find game in ESPN API response"""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                events = data.get("events", [])
                
                for event in events:
                    competitions = event.get("competitions", [])
                    for competition in competitions:
                        competitors = competition.get("competitors", [])
                        
                        if len(competitors) >= 2:
                            home_competitor = next((c for c in competitors if c.get("homeAway") == "home"), None)
                            away_competitor = next((c for c in competitors if c.get("homeAway") == "away"), None)
                            
                            if home_competitor and away_competitor:
                                home_name = home_competitor.get("team", {}).get("displayName", "")
                                away_name = away_competitor.get("team", {}).get("displayName", "")
                                
                                # Match by team names (flexible matching)
                                home_match = (home_team.name.lower() in home_name.lower() or 
                                            home_name.lower() in home_team.name.lower() or
                                            (home_team.city and home_team.city.lower() in home_name.lower()))
                                
                                away_match = (away_team.name.lower() in away_name.lower() or 
                                            away_name.lower() in away_team.name.lower() or
                                            (away_team.city and away_team.city.lower() in away_name.lower()))
                                
                                if home_match and away_match:
                                    return event.get("id")
                
        except Exception as e:
            logger.debug(f"Error trying URL {url}: {e}")
        
        return None
    
    async def _try_team_schedule(self, url, away_team, target_datetime):
        """Try to find game in team schedule"""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                events = data.get("events", [])
                
                for event in events:
                    # Match by date and opponent
                    event_date_str = event.get("date", "")
                    if event_date_str:
                        event_date = datetime.fromisoformat(event_date_str.replace("Z", "+00:00"))
                        
                        # Check if dates are close (within 1 day)
                        if abs((event_date - target_datetime).days) <= 1:
                            competitions = event.get("competitions", [])
                            for competition in competitions:
                                competitors = competition.get("competitors", [])
                                
                                for competitor in competitors:
                                    team_name = competitor.get("team", {}).get("displayName", "")
                                    if (away_team.name.lower() in team_name.lower() or 
                                        team_name.lower() in away_team.name.lower()):
                                        return event.get("id")
                
        except Exception as e:
            logger.debug(f"Error trying team schedule {url}: {e}")
        
        return None
    
    async def collect_game_stats(self, game, espn_game_id):
        """Collect team statistics for a specific game"""
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={espn_game_id}"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    return 0
                
                data = await response.json()
                
                # Extract team stats from boxscore
                boxscore = data.get("boxscore", {})
                teams = boxscore.get("teams", [])
                
                if len(teams) < 2:
                    return 0
                
                stats_added = 0
                
                with SessionLocal() as db:
                    for team_data in teams:
                        team_info = team_data.get("team", {})
                        team_name = team_info.get("displayName", "")
                        statistics = team_data.get("statistics", [])
                        
                        # Find matching team using improved fuzzy matching
                        db_team = None
                        home_team = db.query(Team).filter(Team.team_uid == game.home_team_uid).first()
                        away_team = db.query(Team).filter(Team.team_uid == game.away_team_uid).first()
                        
                        # Try to match by team name with fuzzy matching
                        matched_thesportsdb_id = find_team_by_name_fuzzy(team_name)
                        
                        if matched_thesportsdb_id:
                            if home_team and home_team.team_uid == matched_thesportsdb_id:
                                db_team = home_team
                            elif away_team and away_team.team_uid == matched_thesportsdb_id:
                                db_team = away_team
                        
                        # Fallback to original matching if fuzzy match fails
                        if not db_team:
                            if home_team and (home_team.name.lower() in team_name.lower() or 
                                            team_name.lower() in home_team.name.lower()):
                                db_team = home_team
                            elif away_team and (away_team.name.lower() in team_name.lower() or 
                                              team_name.lower() in away_team.name.lower()):
                                db_team = away_team
                        
                        if db_team and statistics:
                            # Check if stats already exist
                            existing = db.query(TeamGameStat).filter(
                                TeamGameStat.game_uid == game.game_uid,
                                TeamGameStat.team_uid == db_team.team_uid
                            ).first()
                            
                            if not existing:
                                # Convert statistics to dict
                                stats_dict = {}
                                for stat in statistics:
                                    stats_dict[stat.get("name", "")] = stat.get("displayValue", "")
                                
                                # Generate unique stat_uid
                                stat_uid = f"{game.game_uid}_{db_team.team_uid}"
                                
                                # Create new team game stat record
                                team_stat = TeamGameStat(
                                    stat_uid=stat_uid,
                                    game_uid=game.game_uid,
                                    team_uid=db_team.team_uid,
                                    is_home_team=1 if db_team.team_uid == game.home_team_uid else 0,
                                    total_yards=self._safe_int(stats_dict.get("totalYards")),
                                    passing_yards=self._safe_int(stats_dict.get("passingYards")),
                                    rushing_yards=self._safe_int(stats_dict.get("rushingYards")),
                                    turnovers=self._safe_int(stats_dict.get("turnovers")),
                                    penalties=self._safe_int(stats_dict.get("penalties")),
                                    first_downs=self._safe_int(stats_dict.get("firstDowns")),
                                    raw_box_score=stats_dict,
                                    source="ESPN_API"
                                )
                                
                                db.add(team_stat)
                                stats_added += 1
                    
                    if stats_added > 0:
                        db.commit()
                
                return stats_added
                
        except Exception as e:
            logger.error(f"Error collecting stats for game {espn_game_id}: {e}")
            return 0
    
    def _safe_int(self, value):
        """Safely convert value to int"""
        if value is None:
            return None
        try:
            return int(str(value).replace(",", "").split()[0])
        except:
            return None
    
    async def collect_critical_games(self):
        """Collect statistics for all critical missing games"""
        
        # Get critical missing games (exclude preseason)
        with SessionLocal() as db:
            critical_games = db.query(Game).filter(
                ~Game.game_uid.in_(
                    db.query(TeamGameStat.game_uid).distinct()
                ),
                Game.season >= 2022,
                Game.game_datetime.isnot(None),
                # Exclude August preseason games
                ~(extract('month', Game.game_datetime) == 8)
            ).order_by(Game.game_datetime).all()
        
        logger.info(f"🎯 Targeting {len(critical_games)} critical games")
        
        for i, game in enumerate(critical_games, 1):
            try:
                with SessionLocal() as db:
                    home_team = db.query(Team).filter(Team.team_uid == game.home_team_uid).first()
                    away_team = db.query(Team).filter(Team.team_uid == game.away_team_uid).first()
                    
                    if not home_team or not away_team:
                        continue
                    
                    logger.info(f"[{i}/{len(critical_games)}] {away_team.city} {away_team.name} @ {home_team.city} {home_team.name} ({game.game_datetime.date()})")
                    
                    # Try multiple strategies to find ESPN game
                    espn_game_id = await self.find_espn_game_multiple_strategies(game)
                    
                    if espn_game_id:
                        stats_added = await self.collect_game_stats(game, espn_game_id)
                        
                        if stats_added > 0:
                            self.collected_count += 1
                            logger.info(f"  ✅ Added {stats_added} team statistics")
                        else:
                            self.failed_count += 1
                            logger.warning(f"  ⚠️  ESPN game found but no stats added")
                    else:
                        self.failed_count += 1
                        logger.warning(f"  ❌ Could not find ESPN game")
                    
                    # Rate limiting
                    await asyncio.sleep(1.5)
                    
                    # Progress report every 20 games
                    if i % 20 == 0:
                        logger.info(f"📊 Progress: {self.collected_count} collected, {self.failed_count} failed")
                
            except Exception as e:
                logger.error(f"Error processing game {i}: {e}")
                self.failed_count += 1
                continue
        
        logger.info(f"\n🏁 COLLECTION COMPLETE:")
        logger.info(f"   ✅ Successfully collected: {self.collected_count}")
        logger.info(f"   ❌ Failed to collect: {self.failed_count}")
        
        return self.collected_count

async def main():
    logger.info("=" * 80)
    logger.info("CRITICAL GAMES COLLECTOR - TARGETING 147 MISSING GAMES")
    logger.info("=" * 80)
    
    try:
        async with CriticalGamesCollector() as collector:
            collected = await collector.collect_critical_games()
            
            # Final coverage check
            with SessionLocal() as db:
                total_games = db.query(Game).filter(Game.season >= 2022).count()
                preseason_count = db.query(Game).filter(
                    Game.season >= 2022,
                    extract('month', Game.game_datetime) == 8
                ).count()
                legitimate_games = total_games - preseason_count
                games_with_stats = db.query(Game).join(TeamGameStat).filter(Game.season >= 2022).distinct().count()
                
                coverage = (games_with_stats / legitimate_games * 100) if legitimate_games > 0 else 0
                
                logger.info(f"\n📊 FINAL COVERAGE:")
                logger.info(f"   Legitimate games: {legitimate_games}")
                logger.info(f"   Games with stats: {games_with_stats}")
                logger.info(f"   Coverage: {coverage:.1f}%")
                
                if coverage >= 90:
                    logger.info("🎯 EXCELLENT COVERAGE ACHIEVED!")
                elif coverage >= 85:
                    logger.info("✅ Good coverage achieved!")
                else:
                    remaining = legitimate_games - games_with_stats
                    logger.info(f"⚠️  Still missing {remaining} games")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Collection failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)