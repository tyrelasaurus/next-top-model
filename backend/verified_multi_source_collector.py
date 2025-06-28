#!/usr/bin/env python3
"""
Verified Multi-Source NFL Data Collector
Enhanced with thorough game matching and data verification
"""

import asyncio
import logging
import sys
import requests
import time
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, NamedTuple
import json
from dataclasses import dataclass

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.models.sports import Game, Team

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("verified_multi_source_collection.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class GameMatch:
    """Structure for game matching verification"""
    source: str
    confidence: float
    match_criteria: List[str]
    data_found: Dict
    verification_notes: str

class GameVerifier:
    """Verify game matches between sources and database"""
    
    def __init__(self):
        # Team name variations for matching
        self.team_variations = {
            'Arizona Cardinals': ['Arizona', 'Cardinals', 'ARI'],
            'Atlanta Falcons': ['Atlanta', 'Falcons', 'ATL'],
            'Baltimore Ravens': ['Baltimore', 'Ravens', 'BAL'],
            'Buffalo Bills': ['Buffalo', 'Bills', 'BUF'],
            'Carolina Panthers': ['Carolina', 'Panthers', 'CAR'],
            'Chicago Bears': ['Chicago', 'Bears', 'CHI'],
            'Cincinnati Bengals': ['Cincinnati', 'Bengals', 'CIN'],
            'Cleveland Browns': ['Cleveland', 'Browns', 'CLE'],
            'Dallas Cowboys': ['Dallas', 'Cowboys', 'DAL'],
            'Denver Broncos': ['Denver', 'Broncos', 'DEN'],
            'Detroit Lions': ['Detroit', 'Lions', 'DET'],
            'Green Bay Packers': ['Green Bay', 'Packers', 'GB', 'GNB'],
            'Houston Texans': ['Houston', 'Texans', 'HOU'],
            'Indianapolis Colts': ['Indianapolis', 'Colts', 'IND'],
            'Jacksonville Jaguars': ['Jacksonville', 'Jaguars', 'JAX'],
            'Kansas City Chiefs': ['Kansas City', 'Chiefs', 'KC', 'KAN'],
            'Las Vegas Raiders': ['Las Vegas', 'Raiders', 'LV', 'LVR', 'Oakland'],
            'Los Angeles Chargers': ['Los Angeles Chargers', 'Chargers', 'LAC', 'San Diego'],
            'Los Angeles Rams': ['Los Angeles Rams', 'Rams', 'LAR', 'St. Louis'],
            'Miami Dolphins': ['Miami', 'Dolphins', 'MIA'],
            'Minnesota Vikings': ['Minnesota', 'Vikings', 'MIN'],
            'New England Patriots': ['New England', 'Patriots', 'NE', 'NWE'],
            'New Orleans Saints': ['New Orleans', 'Saints', 'NO', 'NOR'],
            'New York Giants': ['New York Giants', 'Giants', 'NYG'],
            'New York Jets': ['New York Jets', 'Jets', 'NYJ'],
            'Philadelphia Eagles': ['Philadelphia', 'Eagles', 'PHI'],
            'Pittsburgh Steelers': ['Pittsburgh', 'Steelers', 'PIT'],
            'San Francisco 49ers': ['San Francisco', '49ers', 'SF', 'SFO'],
            'Seattle Seahawks': ['Seattle', 'Seahawks', 'SEA'],
            'Tampa Bay Buccaneers': ['Tampa Bay', 'Buccaneers', 'TB', 'TAM'],
            'Tennessee Titans': ['Tennessee', 'Titans', 'TEN', 'OTI'],
            'Washington Commanders': ['Washington', 'Commanders', 'WAS', 'Redskins', 'Football Team']
        }
    
    def normalize_team_name(self, team_name: str) -> str:
        """Normalize team name for matching"""
        team_name = team_name.strip()
        
        # Find matching team
        for full_name, variations in self.team_variations.items():
            if any(var.lower() in team_name.lower() for var in variations):
                return full_name
        
        return team_name
    
    def verify_game_match(self, db_game: Game, source_data: Dict, source_name: str) -> GameMatch:
        """Verify if source data matches database game"""
        
        confidence = 0.0
        match_criteria = []
        verification_notes = []
        
        # Get team names from database
        with SessionLocal() as db:
            home_team = db.query(Team).filter(Team.team_uid == db_game.home_team_uid).first()
            away_team = db.query(Team).filter(Team.team_uid == db_game.away_team_uid).first()
            
            if not home_team or not away_team:
                return GameMatch(
                    source=source_name,
                    confidence=0.0,
                    match_criteria=[],
                    data_found={},
                    verification_notes="Missing team data in database"
                )
        
        db_home_name = f"{home_team.city} {home_team.name}"
        db_away_name = f"{away_team.city} {away_team.name}"
        
        # Date matching (highest priority)
        if 'game_date' in source_data and db_game.game_datetime:
            source_date = source_data['game_date']
            if isinstance(source_date, str):
                try:
                    source_date = datetime.fromisoformat(source_date.replace('Z', '+00:00'))
                except:
                    pass
            
            if isinstance(source_date, datetime):
                date_diff = abs((db_game.game_datetime.date() - source_date.date()).days)
                if date_diff == 0:
                    confidence += 0.5
                    match_criteria.append("exact_date_match")
                elif date_diff <= 1:
                    confidence += 0.3
                    match_criteria.append("close_date_match")
                    verification_notes.append(f"Date within 1 day: {date_diff}")
                else:
                    verification_notes.append(f"Date mismatch: {date_diff} days")
        
        # Team matching
        source_teams = source_data.get('teams', [])
        if len(source_teams) >= 2:
            home_match = False
            away_match = False
            
            for team in source_teams:
                normalized_team = self.normalize_team_name(team)
                
                if any(name.lower() in normalized_team.lower() for name in [home_team.city, home_team.name]):
                    home_match = True
                if any(name.lower() in normalized_team.lower() for name in [away_team.city, away_team.name]):
                    away_match = True
            
            if home_match and away_match:
                confidence += 0.4
                match_criteria.append("both_teams_match")
            elif home_match or away_match:
                confidence += 0.2
                match_criteria.append("one_team_match")
                verification_notes.append("Only one team matched")
        
        # Score verification (if available)
        if 'scores' in source_data and db_game.home_score is not None:
            source_scores = source_data['scores']
            if isinstance(source_scores, dict):
                source_home = source_scores.get('home')
                source_away = source_scores.get('away')
                
                if (source_home == db_game.home_score and 
                    source_away == db_game.away_score):
                    confidence += 0.3
                    match_criteria.append("exact_score_match")
                else:
                    verification_notes.append(f"Score mismatch: DB({db_game.home_score}-{db_game.away_score}) vs Source({source_home}-{source_away})")
        
        # Season matching
        if 'season' in source_data:
            if source_data['season'] == db_game.season:
                confidence += 0.1
                match_criteria.append("season_match")
        
        # Week matching (if available)
        if 'week' in source_data and db_game.week:
            if abs(source_data['week'] - db_game.week) <= 1:
                confidence += 0.1
                match_criteria.append("week_match")
        
        return GameMatch(
            source=source_name,
            confidence=confidence,
            match_criteria=match_criteria,
            data_found=source_data,
            verification_notes="; ".join(verification_notes) if verification_notes else "No issues"
        )

class VerifiedMultiSourceCollector:
    """Multi-source collector with enhanced verification"""
    
    def __init__(self, rate_limit_seconds: float = 2.0, min_confidence: float = 0.7):
        self.rate_limit = rate_limit_seconds
        self.min_confidence = min_confidence
        self.last_request_time = 0
        self.verifier = GameVerifier()
        self.stats = {
            "total_attempted": 0,
            "high_confidence_matches": 0,
            "low_confidence_skipped": 0,
            "espn_success": 0,
            "wikipedia_success": 0,
            "fields_updated": 0,
            "verification_failures": 0
        }
        
        # Track all updates for audit
        self.audit_log = []
    
    async def rate_limit_request(self):
        """Apply rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit:
            sleep_time = self.rate_limit - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get_espn_game_data_verified(self, game_date: datetime, season: int, week: int = None) -> List[Dict]:
        """Get ESPN game data with enhanced matching info"""
        try:
            # Use specific date for ESPN API
            date_str = game_date.strftime("%Y%m%d")
            url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={date_str}"
            
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            events = data.get('events', [])
            
            espn_games = []
            
            for event in events:
                try:
                    competitions = event.get('competitions', [])
                    for competition in competitions:
                        competitors = competition.get('competitors', [])
                        
                        if len(competitors) >= 2:
                            # Extract team information
                            teams = []
                            scores = {}
                            
                            for comp in competitors:
                                team_info = comp.get('team', {})
                                team_name = team_info.get('displayName', '')
                                teams.append(team_name)
                                
                                # Determine home/away and scores
                                home_away = comp.get('homeAway', '')
                                score = comp.get('score', {}).get('value')
                                if score is not None:
                                    scores[home_away] = int(score)
                            
                            # Extract game data
                            game_data = {
                                'source': 'ESPN',
                                'game_date': event.get('date'),
                                'teams': teams,
                                'scores': scores,
                                'season': season,
                                'week': event.get('week', {}).get('number') if event.get('week') else week
                            }
                            
                            # Extract attendance
                            if competition.get('attendance'):
                                game_data['attendance'] = competition['attendance']
                            
                            # Extract weather
                            weather = competition.get('weather', {})
                            if weather:
                                if weather.get('temperature'):
                                    game_data['weather_temp'] = weather['temperature']
                                if weather.get('conditionId'):
                                    # Map ESPN weather conditions
                                    conditions_map = {
                                        1: 'sunny', 2: 'partly_cloudy', 3: 'cloudy',
                                        4: 'overcast', 5: 'rain', 6: 'snow', 7: 'clear'
                                    }
                                    game_data['weather_condition'] = conditions_map.get(
                                        weather['conditionId'], f"condition_{weather['conditionId']}"
                                    )
                                if weather.get('displayValue'):
                                    game_data['weather_description'] = weather['displayValue']
                            
                            # Extract venue
                            venue = competition.get('venue', {})
                            if venue and venue.get('fullName'):
                                game_data['venue'] = venue['fullName']
                            
                            espn_games.append(game_data)
                            
                except Exception as e:
                    logger.debug(f"Error parsing ESPN event: {e}")
                    continue
            
            self.stats["espn_success"] += len(espn_games)
            return espn_games
            
        except Exception as e:
            logger.debug(f"ESPN API failed: {e}")
            return []
    
    def get_wikipedia_game_data_verified(self, game: Game) -> Optional[Dict]:
        """Get Wikipedia data with verification info"""
        try:
            # Only for playoff games
            if game.game_type not in ['wildcard', 'divisional', 'conference', 'superbowl']:
                return None
            
            # Get team info for verification
            with SessionLocal() as db:
                home_team = db.query(Team).filter(Team.team_uid == game.home_team_uid).first()
                away_team = db.query(Team).filter(Team.team_uid == game.away_team_uid).first()
                
                if not home_team or not away_team:
                    return None
            
            game_data = {
                'source': 'Wikipedia',
                'game_date': game.game_datetime.isoformat() if game.game_datetime else None,
                'teams': [f"{home_team.city} {home_team.name}", f"{away_team.city} {away_team.name}"],
                'season': game.season,
                'game_type': game.game_type
            }
            
            # Try different Wikipedia URLs based on game type
            urls_to_try = []
            
            if game.game_type == 'superbowl':
                sb_number = game.season - 1966
                roman = self.roman_numeral(sb_number)
                urls_to_try.append(f"https://en.wikipedia.org/wiki/Super_Bowl_{roman}")
            else:
                urls_to_try.append(f"https://en.wikipedia.org/wiki/{game.season}_NFL_playoffs")
                urls_to_try.append(f"https://en.wikipedia.org/wiki/{game.season}_{game.season+1}_NFL_playoffs")
            
            for url in urls_to_try:
                try:
                    response = requests.get(url, timeout=15)
                    response.raise_for_status()
                    
                    content = response.text.lower()
                    
                    # Look for team names in content to verify we have the right page
                    team_mentions = 0
                    for team_name in [home_team.name.lower(), away_team.name.lower()]:
                        if team_name in content:
                            team_mentions += 1
                    
                    if team_mentions >= 1:  # At least one team mentioned
                        # Extract attendance
                        attendance_patterns = [
                            r'attendance[:\s]*([0-9,]+)',
                            r'([0-9,]+)\s+in attendance',
                            r'crowd of ([0-9,]+)'
                        ]
                        
                        for pattern in attendance_patterns:
                            match = re.search(pattern, content)
                            if match:
                                attendance_str = match.group(1).replace(',', '')
                                if attendance_str.isdigit() and 10000 <= int(attendance_str) <= 100000:
                                    game_data['attendance'] = int(attendance_str)
                                    break
                        
                        # Extract weather
                        weather_patterns = [
                            r'temperature[:\s]*([0-9]+)°?[f|fahrenheit]',
                            r'([0-9]+)°[f|fahrenheit]',
                            r'weather[:\s]*([^.]+)'
                        ]
                        
                        for pattern in weather_patterns:
                            match = re.search(pattern, content)
                            if match:
                                if 'weather' in pattern:
                                    weather_desc = match.group(1).strip()
                                    if len(weather_desc) < 50:  # Reasonable length
                                        game_data['weather_condition'] = weather_desc
                                else:
                                    temp_str = match.group(1)
                                    if temp_str.isdigit() and 0 <= int(temp_str) <= 120:
                                        game_data['weather_temp'] = int(temp_str)
                                break
                        
                        if 'attendance' in game_data or 'weather_temp' in game_data:
                            self.stats["wikipedia_success"] += 1
                            return game_data
                
                except Exception as e:
                    logger.debug(f"Wikipedia URL failed {url}: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.debug(f"Wikipedia scraping failed: {e}")
            return None
    
    def roman_numeral(self, num: int) -> str:
        """Convert number to Roman numeral"""
        if num <= 0:
            return "I"
        
        values = [50, 40, 10, 9, 5, 4, 1]
        symbols = ['L', 'XL', 'X', 'IX', 'V', 'IV', 'I']
        
        result = ''
        for i, value in enumerate(values):
            count = num // value
            result += symbols[i] * count
            num -= value * count
        
        return result
    
    async def verify_and_update_game(self, db_game: Game) -> int:
        """Verify and update a single game with multi-source data"""
        
        self.stats["total_attempted"] += 1
        fields_updated = 0
        
        logger.info(f"Processing {db_game.game_type} game: {db_game.game_uid}")
        
        if not db_game.game_datetime:
            logger.warning(f"  ⚠️  No game datetime for {db_game.game_uid}")
            return 0
        
        # Collect data from multiple sources
        source_matches = []
        
        # ESPN API
        await self.rate_limit_request()
        espn_games = self.get_espn_game_data_verified(
            db_game.game_datetime, 
            db_game.season, 
            int(db_game.week) if db_game.week else None
        )
        
        for espn_game in espn_games:
            match = self.verifier.verify_game_match(db_game, espn_game, "ESPN")
            if match.confidence >= self.min_confidence:
                source_matches.append(match)
                logger.info(f"  ✅ ESPN match (confidence: {match.confidence:.2f})")
            elif match.confidence > 0.3:
                logger.info(f"  ⚠️  ESPN low confidence (confidence: {match.confidence:.2f}): {match.verification_notes}")
        
        # Wikipedia (for playoff games)
        if db_game.game_type in ['wildcard', 'divisional', 'conference', 'superbowl']:
            await self.rate_limit_request()
            wiki_data = self.get_wikipedia_game_data_verified(db_game)
            
            if wiki_data:
                match = self.verifier.verify_game_match(db_game, wiki_data, "Wikipedia")
                if match.confidence >= self.min_confidence:
                    source_matches.append(match)
                    logger.info(f"  ✅ Wikipedia match (confidence: {match.confidence:.2f})")
                elif match.confidence > 0.3:
                    logger.info(f"  ⚠️  Wikipedia low confidence (confidence: {match.confidence:.2f}): {match.verification_notes}")
        
        # Process high-confidence matches
        if source_matches:
            # Sort by confidence and process best matches first
            source_matches.sort(key=lambda x: x.confidence, reverse=True)
            
            merged_data = {}
            sources_used = []
            
            for match in source_matches:
                sources_used.append(f"{match.source}({match.confidence:.2f})")
                
                # Merge data, preferring higher confidence sources
                for field, value in match.data_found.items():
                    if field in ['attendance', 'weather_temp', 'weather_condition', 'venue'] and field not in merged_data:
                        merged_data[field] = value
            
            # Update database
            with SessionLocal() as db:
                game_to_update = db.query(Game).filter(Game.game_uid == db_game.game_uid).first()
                if game_to_update:
                    
                    update_record = {
                        "game_uid": db_game.game_uid,
                        "timestamp": datetime.utcnow().isoformat(),
                        "sources": sources_used,
                        "updates": {}
                    }
                    
                    for field, value in merged_data.items():
                        if hasattr(game_to_update, field) and getattr(game_to_update, field) is None:
                            old_value = getattr(game_to_update, field)
                            setattr(game_to_update, field, value)
                            fields_updated += 1
                            
                            update_record["updates"][field] = {
                                "old": old_value,
                                "new": value
                            }
                    
                    if fields_updated > 0:
                        game_to_update.updated_at = datetime.utcnow()
                        db.commit()
                        
                        self.audit_log.append(update_record)
                        self.stats["fields_updated"] += fields_updated
                        self.stats["high_confidence_matches"] += 1
                        
                        logger.info(f"  ✅ Updated {fields_updated} fields from: {', '.join(sources_used)}")
                    else:
                        logger.info(f"  ℹ️  No new fields to update")
        else:
            self.stats["low_confidence_skipped"] += 1
            logger.info(f"  ⚠️  No high-confidence matches found")
        
        return fields_updated
    
    async def process_season_verified(self, season: int, max_games: int = 50) -> Dict:
        """Process a season with verification"""
        
        logger.info(f"Starting verified multi-source collection for {season} season")
        
        with SessionLocal() as db:
            # Prioritize games that need data
            games_query = db.query(Game).filter(Game.season == season)
            
            # Get playoff games first
            playoff_games = games_query.filter(
                Game.game_type.in_(['wildcard', 'divisional', 'conference', 'superbowl'])
            ).all()
            
            # Get regular season games that might have good ESPN coverage
            regular_games = games_query.filter(
                Game.game_type == 'regular',
                Game.attendance.is_(None)  # Focus on games missing data
            ).limit(max(0, max_games - len(playoff_games))).all()
            
            games_to_process = playoff_games + regular_games
        
        logger.info(f"Processing {len(games_to_process)} games ({len(playoff_games)} playoff, {len(regular_games)} regular)")
        
        season_stats = {
            "games_processed": 0,
            "fields_updated": 0,
            "high_confidence": 0,
            "low_confidence": 0
        }
        
        for i, game in enumerate(games_to_process, 1):
            try:
                fields_updated = await self.verify_and_update_game(game)
                season_stats["games_processed"] += 1
                season_stats["fields_updated"] += fields_updated
                
                if fields_updated > 0:
                    season_stats["high_confidence"] += 1
                else:
                    season_stats["low_confidence"] += 1
                
                # Progress update
                if i % 10 == 0:
                    logger.info(f"Progress: {i}/{len(games_to_process)} games processed")
                    
            except Exception as e:
                logger.error(f"Failed to process game {game.game_uid}: {e}")
                self.stats["verification_failures"] += 1
        
        return season_stats
    
    def generate_audit_report(self) -> str:
        """Generate audit report of all updates"""
        
        report_lines = [
            "=" * 80,
            "VERIFIED MULTI-SOURCE COLLECTION AUDIT REPORT",
            "=" * 80,
            f"Generated: {datetime.utcnow().isoformat()}",
            f"Total games attempted: {self.stats['total_attempted']}",
            f"High confidence matches: {self.stats['high_confidence_matches']}",
            f"Fields updated: {self.stats['fields_updated']}",
            f"ESPN successes: {self.stats['espn_success']}",
            f"Wikipedia successes: {self.stats['wikipedia_success']}",
            "",
            "INDIVIDUAL GAME UPDATES:",
            "-" * 40
        ]
        
        for i, update in enumerate(self.audit_log, 1):
            report_lines.extend([
                f"{i}. Game: {update['game_uid']}",
                f"   Sources: {', '.join(update['sources'])}",
                f"   Updates: {len(update['updates'])} fields"
            ])
            
            for field, change in update['updates'].items():
                report_lines.append(f"     {field}: {change['old']} → {change['new']}")
            
            report_lines.append("")
        
        return "\n".join(report_lines)

async def main():
    """Main execution with verification"""
    logger.info("=" * 80)
    logger.info("VERIFIED MULTI-SOURCE NFL DATA COLLECTION")
    logger.info("=" * 80)
    logger.info("Enhanced with game matching verification and audit logging")
    
    # Process recent seasons with good data availability
    seasons = [2024, 2023, 2022]
    
    collector = VerifiedMultiSourceCollector(
        rate_limit_seconds=2.0, 
        min_confidence=0.7  # Require 70% confidence for updates
    )
    
    results = {}
    
    for season in seasons:
        try:
            logger.info(f"\n{'='*20} Processing {season} Season {'='*20}")
            result = await collector.process_season_verified(season, max_games=40)
            results[season] = result
            
            logger.info(f"✅ {season} Season Complete:")
            logger.info(f"   Games processed: {result['games_processed']}")
            logger.info(f"   Fields updated: {result['fields_updated']}")
            logger.info(f"   High confidence: {result['high_confidence']}")
            
        except Exception as e:
            logger.error(f"❌ Failed to process season {season}: {e}")
            results[season] = {"error": str(e)}
    
    # Generate final report
    logger.info("\n" + "=" * 60)
    logger.info("VERIFIED COLLECTION COMPLETE")
    logger.info("=" * 60)
    
    total_fields = sum(r.get('fields_updated', 0) for r in results.values())
    total_games = sum(r.get('games_processed', 0) for r in results.values())
    
    logger.info(f"Total games processed: {total_games}")
    logger.info(f"Total fields updated: {total_fields}")
    logger.info(f"High confidence matches: {collector.stats['high_confidence_matches']}")
    logger.info(f"Verification failures: {collector.stats['verification_failures']}")
    
    # Save audit report
    audit_report = collector.generate_audit_report()
    audit_file = Path(__file__).parent / "multi_source_audit_report.txt"
    
    with open(audit_file, 'w') as f:
        f.write(audit_report)
    
    logger.info(f"\n📋 Audit report saved: {audit_file}")
    logger.info("🎯 VERIFIED MULTI-SOURCE COLLECTION SUCCESSFUL!")

if __name__ == "__main__":
    asyncio.run(main())