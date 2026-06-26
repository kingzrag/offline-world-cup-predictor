
#!/usr/bin/env python3
from curl_cffi import requests
import json

# List of browser impersonations from curl_cffi
BROWSER_IMPERSONATIONS = [
    "chrome",
    "chrome101",
    "chrome104",
    "chrome107",
    "chrome110",
    "chrome116",
    "chrome119",
    "chrome120",
    "chrome123",
    "edge99",
    "edge101",
    "safari15_3",
    "safari15_5",
    "safari16_0",
    "safari17_0",
    "firefox100",
    "firefox101",
    "firefox110",
    "firefox117",
    "firefox120",
]

def test_impersonation(impersonate):
    print(f"\nTesting impersonation: {impersonate}")
    try:
        session = requests.Session(impersonate=impersonate)
        
        # First get main page to get cookies
        main_response = session.get("https://www.sofascore.com", timeout=30)
        print(f"Main page status: {main_response.status_code}")
        
        # Then try API
        api_url = "https://api.sofascore.com/api/v1/sport/football/events/live"
        headers = {
            "Referer": "https://www.sofascore.com",
            "Origin": "https://www.sofascore.com",
            "Accept": "application/json, text/plain, */*",
        }
        api_response = session.get(api_url, headers=headers, timeout=30)
        print(f"API status: {api_response.status_code}")
        
        if api_response.status_code == 200:
            data = api_response.json()
            print(f"Success! Found {len(data.get('events', []))} live events")
            return True
        else:
            print(f"API response: {api_response.text[:200]}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing all browser impersonations...")
    working_impersonations = []
    
    for impersonation in BROWSER_IMPERSONATIONS:
        if test_impersonation(impersonation):
            working_impersonations.append(impersonation)
    
    print("\n" + "=" * 80)
    if working_impersonations:
        print(f"Working impersonations: {working_impersonations}")
    else:
        print("No impersonations worked!")
