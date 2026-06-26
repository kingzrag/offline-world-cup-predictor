
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from collectors.sofascore import SofaScoreCollector
import json

print("Testing updated SofaScoreCollector...")
collector = SofaScoreCollector()

print("\n1. Testing get_live_matches()...")
live = collector.get_live_matches()
if live:
    print(f"Success! Got live data: {json.dumps(live, indent=2)}")
else:
    print("Failed to get live matches")

print("\n2. Testing with a known event ID...")
event_id = 11352313  # Test event
details = collector.get_match_details(event_id)
if details:
    print(f"Success! Got event details: {json.dumps(details, indent=2)[:3000]}")
else:
    print("Failed to get event details")
