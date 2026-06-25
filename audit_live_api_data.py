#!/usr/bin/env python3
import asyncio
import os
import sys

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from database.connection import SessionLocal
from models import Match
from services.collection_service import CollectionService


async def main():
    print("="*120)
    print("API-Football Live Data Audit")
    print("="*120)

    # First, run the live ingestion once
    print("\n1. Running API-Football live ingestion...")
    db = SessionLocal()
    try:
        service = CollectionService()
        summary = await service.ingest_api_football_live(db)
        print(f"✅ Live ingestion complete! Summary: {summary}")
    except Exception as e:
        print(f"❌ Live ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        return
    finally:
        db.close()

    # Now check the data in the DB
    print("\n2. Checking database for live data...")
    db = SessionLocal()
    try:
        # a) Matches with current_minute
        print("\n📊 Matches with current_minute:")
        with_minute = (
            db.query(Match)
            .filter(Match.current_minute.isnot(None))
            .order_by(Match.utc_date.desc())
            .all()
        )
        if with_minute:
            for match in with_minute:
                print(f"  - {match.id}: {match.home_team.name} vs {match.away_team.name} "
                      f"@ minute {match.current_minute}")
        else:
            print("  - No matches with current_minute found.")

        # b) Matches with red cards
        print("\n🔴 Matches with red cards:")
        with_red = (
            db.query(Match)
            .filter((Match.home_red_cards > 0) | (Match.away_red_cards > 0))
            .order_by(Match.utc_date.desc())
            .all()
        )
        if with_red:
            for match in with_red:
                print(f"  - {match.id}: {match.home_team.name} (red: {match.home_red_cards}) vs "
                      f"{match.away_team.name} (red: {match.away_red_cards})")
        else:
            print("  - No matches with red cards found.")

        # c) Matches with api_football_id
        print("\n🆔 Matches with api_football_id:")
        with_api_id = (
            db.query(Match)
            .filter(Match.api_football_id.isnot(None))
            .order_by(Match.utc_date.desc())
            .all()
        )
        if with_api_id:
            for match in with_api_id:
                print(f"  - {match.id}: {match.home_team.name} vs {match.away_team.name} "
                      f"(API Football ID: {match.api_football_id})")
        else:
            print("  - No matches with api_football_id found.")

        # d) Sample live matches
        print("\n📋 Sample live match records:")
        sample_matches = (
            db.query(Match)
            .order_by(Match.utc_date.desc())
            .limit(5)
            .all()
        )
        for match in sample_matches:
            print(f"\n  Match {match.id}:")
            print(f"    Teams: {match.home_team.name} vs {match.away_team.name}")
            print(f"    Status: {match.status}")
            print(f"    Date: {match.utc_date}")
            print(f"    API Football ID: {match.api_football_id}")
            print(f"    Current minute: {match.current_minute}")
            print(f"    Current score: {match.current_home_score} - {match.current_away_score}")
            print(f"    Red cards: Home {match.home_red_cards}, Away {match.away_red_cards}")
            print(f"    Yellow cards: Home {match.home_yellow_cards}, Away {match.away_yellow_cards}")

    finally:
        db.close()

    print("\n" + "="*120)
    print("Audit complete!")
    print("="*120)


if __name__ == "__main__":
    asyncio.run(main())
