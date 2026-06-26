
from sofascore_api import SofaScoreClient
import json

print("Testing SofaScoreClient from pysofascore...")
client = SofaScoreClient()

print("\n1. Testing get_live_events('football')...")
try:
    live = client.get_live_events("football")
    print(f"Success! Got {len(live)} live events")
    if live:
        print(f"First live event: {json.dumps(live[0], indent=2)}")
except Exception as e:
    print(f"Error: {e}")

print("\n2. Testing get_events_today('football')...")
try:
    today = client.get_events_today("football")
    print(f"Success! Got {len(today)} events today")
    if today:
        print(f"First event: {json.dumps(today[0], indent=2)}")
except Exception as e:
    print(f"Error: {e}")

client.close()
