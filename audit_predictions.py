#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timezone
from sqlalchemy.orm import Session

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.connection import SessionLocal
from models import Team
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


def audit_match(db: Session, home_name: str, away_name: str, wc_bundle, goal_bundle, match_date=None):
    """Audit a single match: get features, build vectors, run model"""
    home_team = get_team_id(db, home_name)
    away_team = get_team_id(db, away_name)
    if not home_team:
        raise ValueError(f"Home team not found: {home_name}")
    if not away_team:
        raise ValueError(f"Away team not found: {away_name}")
    
    match_date = match_date or datetime.now(timezone.utc)
    features = extract_ml_features(db, home_team.id, away_team.id, match_date, competition_code="WC")
    
    # Build vectors
    wc_features = wc_bundle.get("features", [])
    goal_features = goal_bundle.get("features", [])
    wc_vector = [features.get(f, 0.0) for f in wc_features]
    goal_vector = [features.get(f, 0.0) for f in goal_features]
    
    # Run models to get predictions
    wc_model = wc_bundle["model"]
    wc_input_df = pd.DataFrame([wc_vector], columns=wc_features)
    raw_probs = wc_model.predict_proba(wc_input_df)[0]
    # Label mapping: 0=Away, 1=Draw, 2=Home
    raw_away, raw_draw, raw_home = raw_probs
    rounded_home = round(raw_home, 4)
    rounded_draw = round(raw_draw, 4)
    rounded_away = round(raw_away, 4)

    # Goal model
    home_xg_model = goal_bundle["home_model"]
    away_xg_model = goal_bundle["away_model"]
    raw_xg_home = float(home_xg_model.predict(np.array([goal_vector]))[0])
    raw_xg_away = float(away_xg_model.predict(np.array([goal_vector]))[0])
    xg_home = max(0.0, raw_xg_home)
    xg_away = max(0.0, raw_xg_away)

    return {
        "match": f"{home_team.name} vs {away_team.name}",
        "home_team_id": home_team.id,
        "away_team_id": away_team.id,
        "features": features,
        "wc_vector": wc_vector,
        "goal_vector": goal_vector,
        "predictions": {
            "raw": {
                "home_win": raw_home,
                "draw": raw_draw,
                "away_win": raw_away,
                "home_xg": raw_xg_home,
                "away_xg": raw_xg_away
            },
            "rounded": {
                "home_win": rounded_home,
                "draw": rounded_draw,
                "away_win": rounded_away,
                "home_xg": round(xg_home, 4),
                "away_xg": round(xg_away, 4)
            }
        }
    }


def main():
    db = SessionLocal()
    try:
        wc_bundle, goal_bundle = load_models()
        
        matches = [
            ("Germany", "Ecuador"),
            ("Bosnia and Herzegovina", "Qatar"),
            ("Scotland", "Brazil")
        ]
        
        print("=" * 160)
        print("END-TO-END PREDICTION TRACE AUDIT REPORT")
        print("=" * 160)
        
        for home, away in matches:
            print("\n" + "-" * 160)
            print(f"MATCH: {home} vs {away}")
            print("-" * 160)
            try:
                audit = audit_match(db, home, away, wc_bundle, goal_bundle)
                
                # Print full extracted features
                print("\n[1/6] Extracted Features:")
                for key, val in sorted(audit["features"].items()):
                    print(f"  {key:<40} = {val}")
                
                # Print WC model vector
                print("\n[2/6] World Cup Model Input Vector:")
                print("  (Features in order used by model):")
                for i, (feat, val) in enumerate(zip(wc_bundle.get("features", []), audit["wc_vector"])):
                    print(f"  {i+1:2d}. {feat:<40} = {val}")
                
                # Print Goal model vector
                print("\n[3/6] Goal Model Input Vector:")
                print("  (Features in order used by model):")
                for i, (feat, val) in enumerate(zip(goal_bundle.get("features", []), audit["goal_vector"])):
                    print(f"  {i+1:2d}. {feat:<40} = {val}")

                # Print predictions
                print("\n[4/6] Raw Model Predictions (no calibration):")
                print(f"  • Home Win: {audit['predictions']['raw']['home_win']:.8f} ({audit['predictions']['raw']['home_win']*100:.4f}%)")
                print(f"  • Draw:     {audit['predictions']['raw']['draw']:.8f} ({audit['predictions']['raw']['draw']*100:.4f}%)")
                print(f"  • Away Win: {audit['predictions']['raw']['away_win']:.8f} ({audit['predictions']['raw']['away_win']*100:.4f}%)")
                print(f"  • Home xG:  {audit['predictions']['raw']['home_xg']:.8f}")
                print(f"  • Away xG:  {audit['predictions']['raw']['away_xg']:.8f}")

                print("\n[5/6] Rounded Predictions (API Response):")
                print(f"  • Home Win: {audit['predictions']['rounded']['home_win']:.4f} ({audit['predictions']['rounded']['home_win']*100:.2f}%)")
                print(f"  • Draw:     {audit['predictions']['rounded']['draw']:.4f} ({audit['predictions']['rounded']['draw']*100:.2f}%)")
                print(f"  • Away Win: {audit['predictions']['rounded']['away_win']:.4f} ({audit['predictions']['rounded']['away_win']*100:.2f}%)")
                print(f"  • Home xG:  {audit['predictions']['rounded']['home_xg']:.4f}")
                print(f"  • Away xG:  {audit['predictions']['rounded']['away_xg']:.4f}")

                print("\n[6/6] Frontend Displayed Probabilities:")
                print(f"  (multiply by 100, no further changes):")
                print(f"  • Home Win: {audit['predictions']['rounded']['home_win']*100:.2f}%")
                print(f"  • Draw:     {audit['predictions']['rounded']['draw']*100:.2f}%")
                print(f"  • Away Win: {audit['predictions']['rounded']['away_win']*100:.2f}%")
                    
            except Exception as e:
                print(f"ERROR auditing match {home} vs {away}: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "=" * 160)
        print("SUMMARY: Probability Changes")
        print("=" * 160)
        print("  1. Raw model probs → Rounded to 4 decimals")
        print("  2. 0-1 → multiplied by 100 for percentage display")
        print("  3. NO other calibration/normalization applied!")
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
