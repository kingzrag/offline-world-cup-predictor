
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from collectors.sofascore import SofaScoreCollector
import json

print("Testing SofaScoreCollector...")
collector = SofaScoreCollector()

print("\n1. Testing get_live_matches...")
live_matches = collector.get_live_matches()
if live_matches:
    print(f"Success! Got {len(live_matches.get('events', []))} live matches")
    if live_matches.get('events'):
        print(f"First live match: {json.dumps(live_matches['events'][0], indent=2)}")
else:
    print("No live matches or failed to fetch")

print("\n2. Testing with a known match ID (11352313 - a past match)...")
match_id = "11352313"
print(f"Getting match details for {match_id}...")
match_details = collector.get_match_details(match_id)
if match_details:
    print("Success! Got match details")
    print(json.dumps(match_details, indent=2)[:3000])
else:
    print("Failed to get match details")
