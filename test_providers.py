#!/usr/bin/env python3
import asyncio
from providers import ProviderOrchestrator


async def main():
    print("Testing provider architecture...")
    orchestrator = ProviderOrchestrator()
    
    print("\n1. Testing get_merged_competitions...")
    competitions = await orchestrator.get_merged_competitions()
    print(f"   Found {len(competitions)} competitions")
    
    print("\n2. Testing get_merged_live_matches...")
    live_matches = await orchestrator.get_merged_live_matches()
    print(f"   Found {len(live_matches)} live matches")
    
    print("\n3. Testing get_merged_competition_matches (WC)...")
    world_cup_matches = await orchestrator.get_merged_competition_matches("WC")
    print(f"   Found {len(world_cup_matches)} World Cup matches")
    
    print("\n✅ Provider architecture test complete!")


if __name__ == "__main__":
    asyncio.run(main())
