
from curl_cffi import requests
from datetime import date
import json

today = date.today().isoformat()
BASE_URL = "https://api.sofascore.com/api/v1"

session = requests.Session(
    impersonate="chrome110",
    headers={
        "Origin": "https://www.sofascore.com",
        "Referer": "https://www.sofascore.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    }
)

print(f"Testing scheduled events for {today}...")
url = f"{BASE_URL}/sport/football/scheduled-events/{today}"
try:
    response = session.get(url, timeout=10)
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Success! Got data:")
        print(f"Number of events: {len(data.get('events', []))}")
        if data.get("events"):
            print("\nFirst event:")
            print(json.dumps(data["events"][0], indent=2))
            
            # Now test event details
            event_id = data["events"][0]["id"]
            print(f"\nTesting event details for event {event_id}...")
            event_url = f"{BASE_URL}/event/{event_id}"
            event_response = session.get(event_url, timeout=10)
            print(f"Event details status code: {event_response.status_code}")
            if event_response.status_code == 200:
                event_data = event_response.json()
                print("\nEvent details:")
                print(json.dumps(event_data, indent=2)[:3000])
except Exception as e:
    print(f"Error: {e}")
