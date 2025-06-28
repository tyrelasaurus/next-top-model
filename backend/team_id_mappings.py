#!/usr/bin/env python3
"""
NFL Team ID Mapping System
Maps between TheSportsDB team IDs (our primary) and other data sources

TheSportsDB team IDs are our primary key system since TheSportsDB is our
foundational data source. Other APIs (ESPN, etc.) need to be mapped to these.
"""

# TheSportsDB Team ID to NFL Abbreviation mapping
THESPORTSDB_TO_NFL = {
    "NFL_134946": "ARI",  # Arizona Cardinals
    "NFL_134942": "ATL",  # Atlanta Falcons
    "NFL_134922": "BAL",  # Baltimore Ravens
    "NFL_134918": "BUF",  # Buffalo Bills
    "NFL_134943": "CAR",  # Carolina Panthers
    "NFL_134938": "CHI",  # Chicago Bears
    "NFL_134923": "CIN",  # Cincinnati Bengals
    "NFL_134924": "CLE",  # Cleveland Browns
    "NFL_134934": "DAL",  # Dallas Cowboys
    "NFL_134930": "DEN",  # Denver Broncos
    "NFL_134927": "DET",  # Detroit Lions
    "NFL_134929": "GB",   # Green Bay Packers
    "NFL_134932": "HOU",  # Houston Texans
    "NFL_134926": "IND",  # Indianapolis Colts
    "NFL_134948": "JAX",  # Jacksonville Jaguars
    "NFL_134944": "KC",   # Kansas City Chiefs
    "NFL_135908": "LV",   # Las Vegas Raiders
    "NFL_134940": "LAC",  # Los Angeles Chargers
    "NFL_134941": "LAR",  # Los Angeles Rams
    "NFL_134920": "MIA",  # Miami Dolphins
    "NFL_134939": "MIN",  # Minnesota Vikings
    "NFL_134921": "NE",   # New England Patriots
    "NFL_134925": "NO",   # New Orleans Saints
    "NFL_134935": "NYG",  # New York Giants
    "NFL_134936": "NYJ",  # New York Jets
    "NFL_134931": "PHI",  # Philadelphia Eagles
    "NFL_134937": "PIT",  # Pittsburgh Steelers
    "NFL_135907": "SF",   # San Francisco 49ers
    "NFL_134949": "SEA",  # Seattle Seahawks
    "NFL_134928": "TB",   # Tampa Bay Buccaneers
    "NFL_134945": "TEN",  # Tennessee Titans
    "NFL_134919": "WAS"   # Washington Commanders
}

# Reverse mapping: NFL Abbreviation to TheSportsDB ID
NFL_TO_THESPORTSDB = {v: k for k, v in THESPORTSDB_TO_NFL.items()}

# ESPN team name to TheSportsDB ID mapping
ESPN_TO_THESPORTSDB = {
    "Arizona Cardinals": "NFL_134946",
    "Atlanta Falcons": "NFL_134942",
    "Baltimore Ravens": "NFL_134922",
    "Buffalo Bills": "NFL_134918",
    "Carolina Panthers": "NFL_134943",
    "Chicago Bears": "NFL_134938",
    "Cincinnati Bengals": "NFL_134923",
    "Cleveland Browns": "NFL_134924",
    "Dallas Cowboys": "NFL_134934",
    "Denver Broncos": "NFL_134930",
    "Detroit Lions": "NFL_134927",
    "Green Bay Packers": "NFL_134929",
    "Houston Texans": "NFL_134932",
    "Indianapolis Colts": "NFL_134926",
    "Jacksonville Jaguars": "NFL_134948",
    "Kansas City Chiefs": "NFL_134944",
    "Las Vegas Raiders": "NFL_135908",
    "Los Angeles Chargers": "NFL_134940",
    "Los Angeles Rams": "NFL_134941",
    "Miami Dolphins": "NFL_134920",
    "Minnesota Vikings": "NFL_134939",
    "New England Patriots": "NFL_134921",
    "New Orleans Saints": "NFL_134925",
    "New York Giants": "NFL_134935",
    "New York Jets": "NFL_134936",
    "Philadelphia Eagles": "NFL_134931",
    "Pittsburgh Steelers": "NFL_134937",
    "San Francisco 49ers": "NFL_135907",
    "Seattle Seahawks": "NFL_134949",
    "Tampa Bay Buccaneers": "NFL_134928",
    "Tennessee Titans": "NFL_134945",
    "Washington Commanders": "NFL_134919"
}

# ESPN API team codes to TheSportsDB ID mapping
ESPN_CODES_TO_THESPORTSDB = {
    "ari": "NFL_134946",
    "atl": "NFL_134942", 
    "bal": "NFL_134922",
    "buf": "NFL_134918",
    "car": "NFL_134943",
    "chi": "NFL_134938",
    "cin": "NFL_134923",
    "cle": "NFL_134924",
    "dal": "NFL_134934",
    "den": "NFL_134930",
    "det": "NFL_134927",
    "gb": "NFL_134929",
    "hou": "NFL_134932",
    "ind": "NFL_134926",
    "jax": "NFL_134948",
    "kc": "NFL_134944",
    "lv": "NFL_135908",
    "lac": "NFL_134940",
    "lar": "NFL_134941",
    "mia": "NFL_134920",
    "min": "NFL_134939",
    "ne": "NFL_134921",
    "no": "NFL_134925",
    "nyg": "NFL_134935",
    "nyj": "NFL_134936",
    "phi": "NFL_134931",
    "pit": "NFL_134937",
    "sf": "NFL_135907",
    "sea": "NFL_134949",
    "tb": "NFL_134928",
    "ten": "NFL_134945",
    "wsh": "NFL_134919"  # ESPN uses 'wsh' for Washington
}

def get_nfl_abbr(thesportsdb_id: str) -> str:
    """Convert TheSportsDB ID to NFL abbreviation"""
    return THESPORTSDB_TO_NFL.get(thesportsdb_id)

def get_thesportsdb_id(nfl_abbr: str) -> str:
    """Convert NFL abbreviation to TheSportsDB ID"""
    return NFL_TO_THESPORTSDB.get(nfl_abbr)

def get_thesportsdb_from_espn_name(espn_name: str) -> str:
    """Convert ESPN team name to TheSportsDB ID"""
    return ESPN_TO_THESPORTSDB.get(espn_name)

def get_thesportsdb_from_espn_code(espn_code: str) -> str:
    """Convert ESPN team code to TheSportsDB ID"""
    return ESPN_CODES_TO_THESPORTSDB.get(espn_code.lower())

def find_team_by_name_fuzzy(team_name: str) -> str:
    """Find TheSportsDB ID by fuzzy matching team name"""
    team_name_lower = team_name.lower()
    
    # Check ESPN names first
    for espn_name, thesportsdb_id in ESPN_TO_THESPORTSDB.items():
        if team_name_lower in espn_name.lower() or espn_name.lower() in team_name_lower:
            return thesportsdb_id
    
    # Check by city/team name components
    name_mappings = {
        "arizona": "NFL_134946", "cardinals": "NFL_134946",
        "atlanta": "NFL_134942", "falcons": "NFL_134942",
        "baltimore": "NFL_134922", "ravens": "NFL_134922",
        "buffalo": "NFL_134918", "bills": "NFL_134918",
        "carolina": "NFL_134943", "panthers": "NFL_134943",
        "chicago": "NFL_134938", "bears": "NFL_134938",
        "cincinnati": "NFL_134923", "bengals": "NFL_134923",
        "cleveland": "NFL_134924", "browns": "NFL_134924",
        "dallas": "NFL_134934", "cowboys": "NFL_134934",
        "denver": "NFL_134930", "broncos": "NFL_134930",
        "detroit": "NFL_134927", "lions": "NFL_134927",
        "green bay": "NFL_134929", "packers": "NFL_134929",
        "houston": "NFL_134932", "texans": "NFL_134932",
        "indianapolis": "NFL_134926", "colts": "NFL_134926",
        "jacksonville": "NFL_134948", "jaguars": "NFL_134948",
        "kansas city": "NFL_134944", "chiefs": "NFL_134944",
        "las vegas": "NFL_135908", "raiders": "NFL_135908",
        "los angeles chargers": "NFL_134940", "chargers": "NFL_134940",
        "los angeles rams": "NFL_134941", "rams": "NFL_134941",
        "miami": "NFL_134920", "dolphins": "NFL_134920",
        "minnesota": "NFL_134939", "vikings": "NFL_134939",
        "new england": "NFL_134921", "patriots": "NFL_134921",
        "new orleans": "NFL_134925", "saints": "NFL_134925",
        "new york giants": "NFL_134935", "giants": "NFL_134935",
        "new york jets": "NFL_134936", "jets": "NFL_134936",
        "philadelphia": "NFL_134931", "eagles": "NFL_134931",
        "pittsburgh": "NFL_134937", "steelers": "NFL_134937",
        "san francisco": "NFL_135907", "49ers": "NFL_135907",
        "seattle": "NFL_134949", "seahawks": "NFL_134949",
        "tampa bay": "NFL_134928", "buccaneers": "NFL_134928",
        "tennessee": "NFL_134945", "titans": "NFL_134945",
        "washington": "NFL_134919", "commanders": "NFL_134919"
    }
    
    for name_part, thesportsdb_id in name_mappings.items():
        if name_part in team_name_lower:
            return thesportsdb_id
    
    return None

def get_all_thesportsdb_ids():
    """Get all TheSportsDB team IDs"""
    return list(THESPORTSDB_TO_NFL.keys())

def get_all_nfl_abbrs():
    """Get all NFL abbreviations"""
    return list(NFL_TO_THESPORTSDB.keys())

if __name__ == "__main__":
    # Test the mappings
    print("Team ID Mapping System")
    print("=" * 40)
    
    print("\nTheSportsDB to NFL mappings:")
    for tsdb_id, nfl_abbr in list(THESPORTSDB_TO_NFL.items())[:5]:
        print(f"  {tsdb_id} -> {nfl_abbr}")
    
    print(f"\nTotal teams mapped: {len(THESPORTSDB_TO_NFL)}")
    
    # Test fuzzy matching
    test_names = ["Kansas City Chiefs", "Los Angeles Rams", "49ers"]
    print("\nFuzzy name matching test:")
    for name in test_names:
        result = find_team_by_name_fuzzy(name)
        nfl_abbr = get_nfl_abbr(result) if result else "Not found"
        print(f"  '{name}' -> {result} ({nfl_abbr})")