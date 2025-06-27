#!/usr/bin/env python3
"""Simple API test without dependencies"""

import requests
import json

def test_various_endpoints():
    """Test different API endpoints to understand what works"""
    
    api_key = "886153"
    
    # Test different endpoint formats
    endpoints = [
        f"https://www.thesportsdb.com/api/v2/json/{api_key}/all/leagues",
        f"https://www.thesportsdb.com/api/v2/json/{api_key}/search/league/nfl",
        f"https://www.thesportsdb.com/api/v1/json/{api_key}/all_leagues.php",
        "https://www.thesportsdb.com/api/v1/json/1/all_leagues.php",  # Free endpoint
        "https://www.thesportsdb.com/api/v1/json/1/search_all_teams.php?l=NFL",  # Free NFL search
    ]
    
    for url in endpoints:
        print(f"\nTesting: {url}")
        try:
            response = requests.get(url, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"Success! Data keys: {list(data.keys()) if data else 'Empty'}")
                    if 'leagues' in data:
                        print(f"Found {len(data['leagues'])} leagues")
                    elif 'teams' in data:
                        print(f"Found {len(data['teams'])} teams")
                except json.JSONDecodeError:
                    print("Response is not valid JSON")
                    print(f"First 200 chars: {response.text[:200]}")
            else:
                print(f"Error response: {response.text[:200]}")
                
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    test_various_endpoints()