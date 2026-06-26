
from sofascore_api import SofaScoreClient
import json

print("Testing pysofascore SofaScoreClient...")
try:
    client = SofaScoreClient()
    
    # Test getting today's events
    print("\nGetting today's events...")
    events = client.get_events_today("football")
    print(f"Got {len(events)} events")
    if events:
        print("First event:")
        print(json.dumps(events[0], indent=2))
    
    # Test getting an event's statistics, lineups, incidents
    if events:
        event_id = events[0]["id"]
        print(f"\nGetting event {event_id} details...")
        stats = client.get_event_statistics(event_id)
        print(f"Got {len(stats)} stat periods")
        
        lineups = client.get_event_lineups(event_id)
        print(f"Got lineups for home and away teams")
        
        incidents = client.get_event_incidents(event_id)
        print(f"Got {len(incidents)} incidents")
    
    client.close()
    print("\nTest completed!")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    print(traceback.format_exc())
