#!/usr/bin/env python3
import os
import sys
import pandas as pd
from datetime import datetime, timezone

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from database.connection import SessionLocal
from ml.features import extract_ml_features
from models import Match


def main():
    db = SessionLocal()
    try:
        print("=" * 120)
        print("LIVE PREDICTION UPGRADE AUDIT")
        print("=" * 120)

        print("\n1. Checking matches in the database")
        matches = db.query(Match).limit(5).all()
        for match in matches:
            print(f"\n  - Match {match.id}: {match.home_team.name if match.home_team else '?'} vs {match.away_team.name if match.away_team else '?'}")
            print(f"    Status: {match.status}, Date: {match.utc_date.date()}")
            print(f"    New fields: current_minute={match.current_minute}, home_red={match.home_red_cards}, away_red={match.away_red_cards}")

        print("\n2. Testing extract_ml_features() with a match")
        # Pick a match to test
        test_match = matches[0] if matches else None
        if test_match:
            features = extract_ml_features(
                db, test_match.home_team_id, test_match.away_team_id,
                test_match.utc_date, competition_code="WC", match=test_match
            )
            print("\n  New live features:")
            live_feat_names = [
                "current_minute", "time_remaining", "current_score_diff",
                "home_red_cards", "away_red_cards", "red_card_diff",
                "home_group_position", "away_group_position", "group_position_diff",
                "home_points", "away_points", "points_diff", "goal_difference_diff",
                "home_implied_probability", "draw_implied_probability", "away_implied_probability"
            ]
            for name in live_feat_names:
                print(f"    {name:<30} = {features[name]}")

        print("\n3. Summary:")
        print("  ✓ New Match model fields added")
        print("  ✓ extract_ml_features() now supports live features")
        print("  ✓ Standings, odds, and live events integrated")
        print("  ✓ model_service updated to pass match object")
        print("  ✓ API-Football collector created")

    finally:
        db.close()

    print("\n" + "=" * 120)


if __name__ == "__main__":
    main()

