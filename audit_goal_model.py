
#!/usr/bin/env python3
import os
import sys
import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from collections import Counter
from sqlalchemy.orm import Session

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from database.connection import SessionLocal
from models import Match, Team, Competition
from ml.features import extract_ml_features


def main():
    db = SessionLocal()
    try:
        print("=" * 160)
        print("GOAL PREDICTION MODEL AUDIT REPORT")
        print("=" * 160)

        # 1. Load model
        print("\n[1/6] Loading goal model...")
        goal_bundle_path = os.path.join(project_root, "models", "goal_predictor.pkl")
        with open(goal_bundle_path, "rb") as f:
            goal_bundle = pickle.load(f)
        goal_features = goal_bundle.get("features", [])
        home_model = goal_bundle["home_model"]
        away_model = goal_bundle["away_model"]
        print(f"   - Goal model features: {len(goal_features)}")

        # 2. Get up to next 500 fixtures (including finished to get larger sample)
        print("\n[2/6] Fetching fixtures (including finished)...")
        matches = (
            db.query(Match)
            .order_by(Match.utc_date.asc())
            .limit(500)
            .all()
        )
        print(f"   - Found {len(matches)} fixtures")

        # 3. Predict all fixtures and collect data
        print("\n[3/6] Running predictions on fixtures...")
        data = []
        for match in matches:
            try:
                # Get features
                features = extract_ml_features(
                    db,
                    match.home_team_id,
                    match.away_team_id,
                    match.utc_date,
                    competition_code=match.competition.code if match.competition else "WC"
                )
                # Prepare input vector
                feature_vals = [features.get(f, 0.0) for f in goal_features]
                feature_vec = np.array([feature_vals])
                # Predict
                raw_home = float(home_model.predict(feature_vec)[0])
                raw_away = float(away_model.predict(feature_vec)[0])
                # Clip
                clipped_home = max(0.0, raw_home)
                clipped_away = max(0.0, raw_away)
                # Final output (rounded to 4 decimals)
                final_home = round(clipped_home, 4)
                final_away = round(clipped_away, 4)
                # Team names
                home_name = match.home_team.name if match.home_team else str(match.home_team_id)
                away_name = match.away_team.name if match.away_team else str(match.away_team_id)
                data.append({
                    "home_team": home_name,
                    "away_team": away_name,
                    "raw_home_xg": raw_home,
                    "raw_away_xg": raw_away,
                    "clipped_home_xg": clipped_home,
                    "clipped_away_xg": clipped_away,
                    "final_home_xg": final_home,
                    "final_away_xg": final_away,
                    "home_clipped": raw_home < 0,
                    "away_clipped": raw_away < 0
                })
            except Exception as e:
                print(f"   - Warning: Skipping match {match.id}: {e}")
                continue
        print(f"   - Successfully processed {len(data)} fixtures")

        # 4. Calculate statistics
        print("\n[4/6] Calculating statistics...")
        df = pd.DataFrame(data)
        # Count stats
        home_zero = (df["final_home_xg"] == 0.0).sum()
        away_zero = (df["final_away_xg"] == 0.0).sum()
        home_low = (df["final_home_xg"] < 0.1).sum()
        away_low = (df["final_away_xg"] < 0.1).sum()
        home_high = (df["final_home_xg"] > 3.0).sum()
        away_high = (df["final_away_xg"] > 3.0).sum()
        home_clipped_count = df["home_clipped"].sum()
        away_clipped_count = df["away_clipped"].sum()

        print("\n--- COUNTS ---")
        print(f"Home xG == 0.0: {home_zero} ({home_zero / len(df) * 100:.2f}%)")
        print(f"Away xG == 0.0: {away_zero} ({away_zero / len(df) * 100:.2f}%)")
        print(f"Home xG < 0.1: {home_low} ({home_low / len(df) * 100:.2f}%)")
        print(f"Away xG < 0.1: {away_low} ({away_low / len(df) * 100:.2f}%)")
        print(f"Home xG > 3.0: {home_high} ({home_high / len(df) * 100:.2f}%)")
        print(f"Away xG > 3.0: {away_high} ({away_high / len(df) * 100:.2f}%)")
        print(f"Home predictions clipped to 0: {home_clipped_count} ({home_clipped_count / len(df) * 100:.2f}%)")
        print(f"Away predictions clipped to 0: {away_clipped_count} ({away_clipped_count / len(df) * 100:.2f}%)")

        # Distribution stats
        print("\n--- DISTRIBUTION ---")
        print("\nHome xG:")
        print(df["raw_home_xg"].describe())
        print("\nAway xG:")
        print(df["raw_away_xg"].describe())

        # Examples of clipped, zero, and high predictions
        print("\n--- EXAMPLES ---")
        # Clipped examples
        print("\n1. Examples of clipped predictions (raw < 0):")
        clipped_df = df[(df["home_clipped"]) | (df["away_clipped"])].head(5)
        for idx, row in clipped_df.iterrows():
            print(f"\n   - {row['home_team']} vs {row['away_team']}:")
            if row['home_clipped']:
                print(f"     Home: raw={row['raw_home_xg']:.6f} → clipped={row['clipped_home_xg']:.4f} → final={row['final_home_xg']}")
            if row['away_clipped']:
                print(f"     Away: raw={row['raw_away_xg']:.6f} → clipped={row['clipped_away_xg']:.4f} → final={row['final_away_xg']}")
        # Zero examples
        print("\n2. Examples of final xG == 0.0:")
        zero_df = df[(df["final_home_xg"] == 0.0) | (df["final_away_xg"] == 0.0)].head(5)
        for idx, row in zero_df.iterrows():
            print(f"\n   - {row['home_team']} vs {row['away_team']}:")
            if row['final_home_xg'] == 0.0:
                print(f"     Home: raw={row['raw_home_xg']:.6f} → clipped={row['clipped_home_xg']:.4f} → final={row['final_home_xg']}")
            if row['final_away_xg'] == 0.0:
                print(f"     Away: raw={row['raw_away_xg']:.6f} → clipped={row['clipped_away_xg']:.4f} → final={row['final_away_xg']}")
        # High examples
        print("\n3. Examples of xG > 3.0:")
        high_df = df[(df["final_home_xg"] > 3.0) | (df["final_away_xg"] > 3.0)].head(5)
        for idx, row in high_df.iterrows():
            print(f"\n   - {row['home_team']} vs {row['away_team']}:")
            if row['final_home_xg'] > 3.0:
                print(f"     Home: raw={row['raw_home_xg']:.6f} → clipped={row['clipped_home_xg']:.4f} → final={row['final_home_xg']}")
            if row['final_away_xg'] > 3.0:
                print(f"     Away: raw={row['raw_away_xg']:.6f} → clipped={row['clipped_away_xg']:.4f} → final={row['final_away_xg']}")

        # 5. Calibration evaluation
        print("\n[5/6] Calibration evaluation...")
        print("\n--- CALIBRATION ---")
        print("Key observations:")
        print(f"- {home_clipped_count + away_clipped_count} predictions are negative and being clipped to zero")
        print(f"- {home_low + away_low} predictions are below 0.1")
        print("- The model uses regression with xgboost on untransformed goals, which can produce negative values")

        # 6. Recommendations
        print("\n[6/6] Recommendations...")
        print("\n--- RECOMMENDATIONS ---")
        print("1. Log-transform targets (best option):")
        print("   - Log-transform actual goals (log(1 + goals)) to ensure non-negative outputs")
        print("   - Retrain the model on log-transformed targets")
        print("   - When predicting, exponentiate to get back to xG (using exp(pred) - 1 or exp(pred))")
        print("2. Minimum floor (0.05):")
        print("   - Quick fix for production: set a minimum xG of 0.05 to avoid 0.0 values")
        print("3. Poisson regression:")
        print("   - Use XGBoost with Poisson objective (objective='count:poisson') which is designed for count data like goals")
        print("4. Retrain:")
        print("   - Ensure training data is representative of current tournament teams")

        # Save data to CSV for further analysis
        output_path = os.path.join(project_root, "goal_model_audit_data.csv")
        df.to_csv(output_path, index=False)
        print(f"\n✅ Data saved to: {output_path}")

    finally:
        db.close()
    print("\n" + "=" * 160)
    print("AUDIT COMPLETE!")
    print("=" * 160)


if __name__ == "__main__":
    main()
