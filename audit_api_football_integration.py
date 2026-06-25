#!/usr/bin/env python3
import os
import sys
import pickle

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from database.connection import SessionLocal
from models import Match
from ml.features import extract_ml_features
from datetime import datetime, timezone

def check_model_features():
    print("="*100)
    print("MODEL FEATURE CHECK")
    print("="*100)
    print("\n--- Goal Predictor ---")
    with open(os.path.join(project_root, "models", "goal_predictor.pkl"), "rb") as f:
        goal_bundle = pickle.load(f)
    print(f"Goal model features (count={len(goal_bundle['features'])}):")
    print(goal_bundle['features'])
    
    print("\n--- World Cup Predictor ---")
    with open(os.path.join(project_root, "models", "world_cup_predictor.pkl"), "rb") as f:
        wc_bundle = pickle.load(f)
    print(f"World Cup model features (count={len(wc_bundle['features'])}):")
    print(wc_bundle['features'])

def check_db_fields():
    db = SessionLocal()
    try:
        print("\n" + "="*100)
        print("DATABASE FIELDS CHECK")
        print("="*100)
        sample_match = db.query(Match).first()
        if sample_match:
            print(f"\nFirst match in DB: {sample_match.id} ({sample_match.home_team.name if sample_match.home_team else ''} vs {sample_match.away_team.name if sample_match.away_team else ''})")
            new_fields = [
                "api_football_id",
                "current_minute",
                "home_red_cards",
                "away_red_cards",
                "home_yellow_cards",
                "away_yellow_cards",
                "current_home_score",
                "current_away_score"
            ]
            print("\nChecking new match fields:")
            for field in new_fields:
                val = getattr(sample_match, field, None)
                print(f"  - {field:<25} = {repr(val)}")
    finally:
        db.close()

def check_collector_integration():
    print("\n" + "="*100)
    print("COLLECTOR INTEGRATION CHECK")
    print("="*100)
    
    print("\n--- Checking imports ---")
    import services.collection_service
    from inspect import getsource
    coll_source = getsource(services.collection_service)
    
    print("\nCollection Service imports:")
    if "APIFootballCollector" in coll_source:
        print("  ✓ APIFootballCollector is imported")
    else:
        print("  ❌ APIFootballCollector is NOT imported")
        
    if "api_football" in coll_source:
        print("  ✓ api_football module referenced")
    else:
        print("  ❌ api_football module NOT referenced")
        
    print("\n--- Checking if collector is initialized ---")
    if "APIFootballCollector(" in coll_source:
        print("  ✓ APIFootballCollector initialized in CollectionService")
    else:
        print("  ❌ APIFootballCollector NOT initialized in CollectionService")

def check_extract_ml_features_has_new_features():
    print("\n" + "="*100)
    print("FEATURE EXTRACTION CHECK")
    print("="*100)
    db = SessionLocal()
    try:
        sample_match = db.query(Match).first()
        if sample_match:
            features = extract_ml_features(
                db, sample_match.home_team_id, sample_match.away_team_id,
                sample_match.utc_date, competition_code="WC", match=sample_match
            )
            
            new_features = [
                "current_minute", "time_remaining", "current_score_diff",
                "home_red_cards", "away_red_cards", "red_card_diff",
                "home_group_position", "away_group_position", "group_position_diff",
                "home_points", "away_points", "points_diff", "goal_difference_diff",
                "home_implied_probability", "draw_implied_probability", "away_implied_probability"
            ]
            
            print("\nNew features in extract_ml_features():")
            for feat in new_features:
                present = feat in features
                status = "✓" if present else "❌"
                value = features.get(feat, "N/A")
                print(f"  {status} {feat:<40} = {value}")
    finally:
        db.close()

def main():
    check_model_features()
    check_db_fields()
    check_collector_integration()
    check_extract_ml_features_has_new_features()
    
    print("\n" + "="*100)
    print("FINAL AUDIT RESULTS")
    print("="*100)

if __name__ == "__main__":
    main()
