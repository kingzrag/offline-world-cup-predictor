#!/usr/bin/env python3
import requests
import json

BASE_URL = "https://api.sofascore.com/api/v1"
TEST_MATCH_ID = "11352314"  # Argentina vs France 2022 WC

# Try multiple User-Agents
USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def test_with_headers(headers):
    print(f"\nTesting with headers: {headers}")
    try:
        # Test live matches endpoint
        print("1. Testing live matches endpoint...")
        live_response = requests.get(f"{BASE_URL}/sport/football/live", headers=headers, timeout=30)
        print(f"   Live matches status: {live_response.status_code}")
        
        # Test match details
        print(f"\n2. Testing match details for ID {TEST_MATCH_ID}...")
        match_response = requests.get(f"{BASE_URL}/event/{TEST_MATCH_ID}", headers=headers, timeout=30)
        print(f"   Match details status: {match_response.status_code}")
        
        if match_response.status_code == 200:
            match_data = match_response.json()
            print(f"   Response keys: {list(match_data.keys())}")
            print("   Saving match data to test_match_data.json...")
            with open("test_match_data.json", "w") as f:
                json.dump(match_data, f, indent=2)
        
        # Test match statistics
        print("\n3. Testing match statistics...")
        stats_response = requests.get(f"{BASE_URL}/event/{TEST_MATCH_ID}/statistics", headers=headers, timeout=30)
        print(f"   Statistics status: {stats_response.status_code}")
        
        if stats_response.status_code == 200:
            stats_data = stats_response.json()
            print("   Saving statistics to test_stats_data.json...")
            with open("test_stats_data.json", "w") as f:
                json.dump(stats_data, f, indent=2)
        
        # Test match incidents
        print("\n4. Testing match incidents (events)...")
        incidents_response = requests.get(f"{BASE_URL}/event/{TEST_MATCH_ID}/incidents", headers=headers, timeout=30)
        print(f"   Incidents status: {incidents_response.status_code}")
        
        if incidents_response.status_code == 200:
            incidents_data = incidents_response.json()
            print("   Saving incidents to test_incidents_data.json...")
            with open("test_incidents_data.json", "w") as f:
                json.dump(incidents_data, f, indent=2)
        
        # Test match lineups
        print("\n5. Testing match lineups...")
        lineups_response = requests.get(f"{BASE_URL}/event/{TEST_MATCH_ID}/lineups", headers=headers, timeout=30)
        print(f"   Lineups status: {lineups_response.status_code}")
        
        if lineups_response.status_code == 200:
            lineups_data = lineups_response.json()
            print("   Saving lineups to test_lineups_data.json...")
            with open("test_lineups_data.json", "w") as f:
                json.dump(lineups_data, f, indent=2)
                
    except Exception as e:
        print(f"   Error: {e}")

for i, user_agent in enumerate(USER_AGENTS):
    print("="*80)
    print(f"Test iteration {i+1}")
    print("="*80)
    test_with_headers({
        "User-Agent": user_agent,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.sofascore.com/",
        "Origin": "https://www.sofascore.com",
        "Connection": "keep-alive"
    })
