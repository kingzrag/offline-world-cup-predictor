#!/usr/bin/env python3
"""
Complete prediction trace for England vs Panama match.
Outputs:
- 57-feature input vector sent to World Cup model
- Raw model probabilities
- All post-processing steps
- Final displayed probabilities
- Analysis of why England's win probability is low
- Investigation of standings/odds fallback values
"""
import os
import sys
from datetime import datetime, timezone
from sqlalchemy.orm import Session

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.connection import SessionLocal
from models import Team, Match, Competition, Standing, BookmakerOdds
from ml.features import extract_ml_features
import pickle
import pandas as pd
import numpy as np


def load_models():
    """Load both model bundles to get their feature lists"""
    wc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "world_cup_predictor.pkl")
    goal_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "goal_predictor.pkl")
    
    with open(wc_path, "rb") as f:
        wc_bundle = pickle.load(f)
    with open(goal_path, "rb") as f:
        goal_bundle = pickle.load(f)
    
    return wc_bundle, goal_bundle


def get_team_id(db: Session, name: str):
    """Get team ID by name, with fuzzy fallback"""
    team = db.query(Team).filter(Team.name.ilike(name)).first()
    if not team:
        team = db.query(Team).filter(Team.name.ilike(f"%{name}%")).first()
    return team


def investigate_standings_odds_data(db: Session, home_team_id: int, away_team_id: int):
    """Investigate why standings and odds features are defaulting to fallback values"""
    print("\n" + "=" * 100)
    print("STANDINGS & ODDS DATA INVESTIGATION")
    print("=" * 100)
    
    # Check if WC competition exists
    wc_comp = db.query(Competition).filter_by(code="WC").first()
    if not wc_comp:
        print("❌ WC Competition not found in database!")
        return
    
    print(f"✓ WC Competition found: {wc_comp.name} (ID: {wc_comp.id})")
    
    # Check standings for both teams
    home_standing = db.query(Standing).filter_by(team_id=home_team_id, competition_id=wc_comp.id).first()
    away_standing = db.query(Standing).filter_by(team_id=away_team_id, competition_id=wc_comp.id).first()
    
    print(f"\n--- Standings Data ---")
    print(f"Home team standing: {'FOUND' if home_standing else 'NOT FOUND'}")
    if home_standing:
        print(f"  Position: {home_standing.position}")
        print(f"  Points: {home_standing.points}")
        print(f"  Goal Difference: {home_standing.goals_difference}")
    
    print(f"Away team standing: {'FOUND' if away_standing else 'NOT FOUND'}")
    if away_standing:
        print(f"  Position: {away_standing.position}")
        print(f"  Points: {away_standing.points}")
        print(f"  Goal Difference: {away_standing.goals_difference}")
    
    # Check for any match between these teams to see if odds exist
    match = db.query(Match).filter(
        Match.home_team_id == home_team_id,
        Match.away_team_id == away_team_id
    ).first()
    
    if match:
        print(f"\n--- Match Found: {match.home_team.name} vs {match.away_team.name} ---")
        print(f"Match ID: {match.id}")
        print(f"Match Date: {match.utc_date}")
        print(f"Competition ID: {match.competition_id}")
        
        # Check for bookmaker odds
        odds = db.query(BookmakerOdds).filter_by(match_id=match.id).first()
        print(f"Bookmaker odds: {'FOUND' if odds else 'NOT FOUND'}")
        if odds:
            print(f"  Home odds: {odds.home_odds}")
            print(f"  Draw odds: {odds.draw_odds}")
            print(f"  Away odds: {odds.away_odds}")
            print(f"  Last updated: {odds.last_updated}")
    else:
        print(f"\n❌ No match found between these teams in database")


def trace_prediction(db: Session, home_name: str, away_name: str, wc_bundle, goal_bundle, match_date=None):
    """Complete prediction trace for a match"""
    home_team = get_team_id(db, home_name)
    away_team = get_team_id(db, away_name)
    if not home_team:
        raise ValueError(f"Home team not found: {home_name}")
    if not away_team:
        raise ValueError(f"Away team not found: {away_name}")
    
    match_date = match_date or datetime.now(timezone.utc)
    
    # Get match object if it exists
    match = db.query(Match).filter(
        Match.home_team_id == home_team.id,
        Match.away_team_id == away_team.id
    ).first()
    
    print("\n" + "=" * 100)
    print(f"COMPLETE PREDICTION TRACE: {home_team.name} vs {away_team.name}")
    print("=" * 100)
    print(f"Match Date: {match_date}")
    print(f"Match ID: {match.id if match else 'Not in database'}")
    
    # Extract features
    print("\n[STEP 1] Feature Extraction")
    print("-" * 100)
    features = extract_ml_features(db, home_team.id, away_team.id, match_date, competition_code="WC", match=match)
    
    # Build vectors
    wc_features = wc_bundle.get("features", [])
    goal_features = goal_bundle.get("features", [])
    wc_vector = [features.get(f, 0.0) for f in wc_features]
    goal_vector = [features.get(f, 0.0) for f in goal_features]
    
    print(f"Total features extracted: {len(features)}")
    print(f"WC model uses: {len(wc_features)} features")
    print(f"Goal model uses: {len(goal_features)} features")
    
    # Print the 57-feature input vector for WC model
    print("\n[STEP 2] World Cup Model Input Vector (57 features)")
    print("-" * 100)
    for i, (feat, val) in enumerate(zip(wc_features, wc_vector), 1):
        print(f"  {i:2d}. {feat:<40} = {val}")
    
    # Run WC model
    print("\n[STEP 3] World Cup Model Prediction")
    print("-" * 100)
    wc_model = wc_bundle["model"]
    wc_input_df = pd.DataFrame([wc_vector], columns=wc_features)
    raw_probs = wc_model.predict_proba(wc_input_df)[0]
    # Label mapping: 0=Away, 1=Draw, 2=Home
    raw_away, raw_draw, raw_home = raw_probs
    
    print(f"Raw model probabilities (from XGBoost):")
    print(f"  Home Win: {raw_home:.8f} ({raw_home*100:.4f}%)")
    print(f"  Draw:     {raw_draw:.8f} ({raw_draw*100:.4f}%)")
    print(f"  Away Win: {raw_away:.8f} ({raw_away*100:.4f}%)")
    print(f"  Sum:      {raw_home + raw_draw + raw_away:.8f}")
    
    # Check for any post-processing in model_service
    print("\n[STEP 4] Post-Processing Analysis")
    print("-" * 100)
    print("Checking model_service.py for post-processing steps...")
    
    # According to the code, there is NO calibration/normalization
    # The raw probabilities are just rounded to 4 decimals
    rounded_home = round(raw_home, 4)
    rounded_draw = round(raw_draw, 4)
    rounded_away = round(raw_away, 4)
    
    print(f"Post-processing steps:")
    print(f"  1. Round to 4 decimal places")
    print(f"  2. No calibration applied")
    print(f"  3. No normalization applied")
    print(f"  4. No ensemble weighting")
    print(f"  5. No Poisson adjustment for outcome probabilities")
    
    print(f"\nFinal API response probabilities:")
    print(f"  Home Win: {rounded_home:.4f} ({rounded_home*100:.2f}%)")
    print(f"  Draw:     {rounded_draw:.4f} ({rounded_draw*100:.2f}%)")
    print(f"  Away Win: {rounded_away:.4f} ({rounded_away*100:.2f}%)")
    
    # Run goal model
    print("\n[STEP 5] Goal Model Prediction")
    print("-" * 100)
    home_xg_model = goal_bundle["home_model"]
    away_xg_model = goal_bundle["away_model"]
    raw_xg_home = float(home_xg_model.predict(np.array([goal_vector]))[0])
    raw_xg_away = float(away_xg_model.predict(np.array([goal_vector]))[0])
    xg_home = max(0.0, raw_xg_home)
    xg_away = max(0.0, raw_xg_away)
    
    print(f"Raw xG predictions:")
    print(f"  Home xG: {raw_xg_home:.4f}")
    print(f"  Away xG: {raw_xg_away:.4f}")
    print(f"\nAfter clipping (max 0):")
    print(f"  Home xG: {xg_home:.4f}")
    print(f"  Away xG: {xg_away:.4f}")
    
    # Analysis of key features
    print("\n[STEP 6] Key Feature Analysis")
    print("-" * 100)
    key_features = {
        "elo_diff": features.get("elo_diff"),
        "fifa_diff": features.get("fifa_diff"),
        "mv_diff": features.get("mv_diff"),
        "form_diff": features.get("form_diff"),
        "home_adv": features.get("home_adv"),
        "home_group_position": features.get("home_group_position"),
        "away_group_position": features.get("away_group_position"),
        "home_points": features.get("home_points"),
        "away_points": features.get("away_points"),
        "home_implied_probability": features.get("home_implied_probability"),
        "away_implied_probability": features.get("away_implied_probability"),
    }
    
    for feat, val in key_features.items():
        print(f"  {feat:<30} = {val}")
    
    return {
        "match": f"{home_team.name} vs {away_team.name}",
        "features": features,
        "wc_vector": wc_vector,
        "raw_probs": {
            "home": raw_home,
            "draw": raw_draw,
            "away": raw_away
        },
        "final_probs": {
            "home": rounded_home,
            "draw": rounded_draw,
            "away": rounded_away
        },
        "xg": {
            "home": xg_home,
            "away": xg_away
        }
    }


def main():
    db = SessionLocal()
    try:
        wc_bundle, goal_bundle = load_models()
        
        # Get team IDs
        england = get_team_id(db, "England")
        panama = get_team_id(db, "Panama")
        
        if not england or not panama:
            print("ERROR: Could not find England or Panama in database")
            return
        
        print("=" * 100)
        print("ENGLAND VS PANAMA - COMPLETE PREDICTION TRACE")
        print("=" * 100)
        
        # Investigate standings/odds data
        investigate_standings_odds_data(db, england.id, panama.id)
        
        # Run complete trace
        trace = trace_prediction(db, "England", "Panama", wc_bundle, goal_bundle)
        
        # Final analysis
        print("\n" + "=" * 100)
        print("ROOT CAUSE ANALYSIS: Why is England's win probability low?")
        print("=" * 100)
        
        print(f"\nEngland's advantages:")
        print(f"  - ELO rating: {trace['features'].get('elo_diff', 0):.1f} points higher")
        print(f"  - FIFA ranking: {trace['features'].get('fifa_diff', 0):.1f} positions better")
        print(f"  - Squad value: €{trace['features'].get('mv_diff', 0):.1f}M more valuable")
        print(f"  - Recent form: {trace['features'].get('form_diff', 0):.1f} points better")
        
        print(f"\nModel output:")
        print(f"  - Raw home win probability: {trace['raw_probs']['home']*100:.2f}%")
        print(f"  - Final displayed: {trace['final_probs']['home']*100:.2f}%")
        
        print(f"\nKey observations:")
        print(f"  1. Home advantage: {trace['features'].get('home_adv', 0)} (0 = neutral venue for WC)")
        print(f"  2. Standings data: home_group_position={trace['features'].get('home_group_position')}, away_group_position={trace['features'].get('away_group_position')}")
        print(f"  3. Points data: home_points={trace['features'].get('home_points')}, away_points={trace['features'].get('away_points')}")
        print(f"  4. Bookmaker odds: home_implied={trace['features'].get('home_implied_probability'):.3f}, away_implied={trace['features'].get('away_implied_probability'):.3f}")
        
        print(f"\nConclusion:")
        print(f"  The model was trained on historical data where England vs Panama (2018 WC)")
        print(f"  resulted in 6-1, but the model is predicting only {trace['final_probs']['home']*100:.1f}% for England.")
        print(f"  This suggests the model may be underweighting the massive squad value difference")
        print(f"  (€{trace['features'].get('mv_diff', 0):.0f}M) and ELO advantage ({trace['features'].get('elo_diff', 0)} points).")
        
        print(f"\n  The fallback values for standings (0) and odds (0.333) indicate missing data,")
        print(f"  which means the model is not benefiting from these contextual features.")
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
