#!/usr/bin/env python3
"""
Verify versioned retrained model bundles load and produce predictions.
"""

from __future__ import annotations

import argparse
import math
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import desc

from database.connection import SessionLocal
from ml.features import extract_ml_features
from models import Competition, Match

PROJECT_ROOT = Path(__file__).resolve().parent
WC_V2_PATH = PROJECT_ROOT / "models" / "world_cup_predictor_v2.pkl"
GOAL_V2_PATH = PROJECT_ROOT / "models" / "goal_predictor_v2.pkl"
WC_CURRENT_PATH = PROJECT_ROOT / "models" / "world_cup_predictor.pkl"
GOAL_CURRENT_PATH = PROJECT_ROOT / "models" / "goal_predictor.pkl"
INTERNATIONAL_CODES = {
    "AFCON",
    "AFCONQ",
    "ASIAN",
    "ASIANQ",
    "CA",
    "CNL",
    "EC",
    "EU",
    "EUQ",
    "FRI",
    "OLY",
    "UNL",
    "WC",
    "WCQ",
    "WCQA",
    "WCQC",
    "WCQE",
    "WWC",
}


def pick_match(db, match_id: int | None) -> Match | None:
    if match_id:
        return db.query(Match).filter(Match.id == match_id).first()
    return (
        db.query(Match)
        .join(Competition, Competition.id == Match.competition_id)
        .filter(
            Match.status == "FINISHED",
            Match.home_score.isnot(None),
            Match.away_score.isnot(None),
            Competition.code.in_(INTERNATIONAL_CODES),
        )
        .order_by(desc(Match.utc_date), desc(Match.id))
        .first()
    )


def ensure_finite(values) -> None:
    for value in values:
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            raise ValueError(f"Non-finite value encountered: {value}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify model bundles load and predict"
    )
    parser.add_argument(
        "--match-id", type=int, help="Specific match ID to verify against"
    )
    parser.add_argument(
        "--wc-model", default=str(WC_V2_PATH), help="Path to world cup model bundle"
    )
    parser.add_argument(
        "--goal-model", default=str(GOAL_V2_PATH), help="Path to goal model bundle"
    )
    args = parser.parse_args()

    wc_path = Path(args.wc_model)
    goal_path = Path(args.goal_model)
    if not wc_path.exists():
        raise FileNotFoundError(f"Missing {wc_path}")
    if not goal_path.exists():
        raise FileNotFoundError(f"Missing {goal_path}")

    with open(wc_path, "rb") as handle:
        wc_bundle = pickle.load(handle)
    with open(goal_path, "rb") as handle:
        goal_bundle = pickle.load(handle)

    db = SessionLocal()
    try:
        match = pick_match(db, args.match_id)
        if not match:
            raise RuntimeError(
                "No suitable international match found for verification."
            )

        features = extract_ml_features(
            db,
            match.home_team_id,
            match.away_team_id,
            match.utc_date,
            competition_code=match.competition.code if match.competition else "WC",
            match_stage=match.stage,
            match=match,
        )

        wc_features = wc_bundle["features"]
        goal_features = goal_bundle["features"]
        wc_vector = [features.get(name, 0.0) for name in wc_features]
        goal_vector = [features.get(name, 0.0) for name in goal_features]
        ensure_finite(wc_vector)
        ensure_finite(goal_vector)

        wc_model = wc_bundle["model"]
        home_goal_model = goal_bundle["home_model"]
        away_goal_model = goal_bundle["away_model"]

        wc_input = pd.DataFrame([wc_vector], columns=wc_features)
        goal_input = np.array([goal_vector], dtype=float)

        probs = wc_model.predict_proba(wc_input)[0]
        home_goal = max(0.0, float(home_goal_model.predict(goal_input)[0]))
        away_goal = max(0.0, float(away_goal_model.predict(goal_input)[0]))

        print("=" * 100)
        print("RETRAINED MODEL VERIFICATION")
        print("=" * 100)
        print(f"Match ID: {match.id}")
        print(f"Fixture:  {match.home_team.name} vs {match.away_team.name}")
        print(f"Date:     {match.utc_date}")
        print()
        print(f"World Cup model path: {wc_path}")
        print(f"Goal model path:      {goal_path}")
        print(f"World Cup version:    {wc_bundle.get('version')}")
        print(f"Goal version:         {goal_bundle.get('version')}")
        print(f"WC feature count:     {len(wc_features)}")
        print(f"Goal feature count:   {len(goal_features)}")
        print()
        print("1X2 probabilities")
        print(f"- Away Win: {float(probs[0]):.6f}")
        print(f"- Draw:     {float(probs[1]):.6f}")
        print(f"- Home Win: {float(probs[2]):.6f}")
        print(f"- Sum:      {float(np.sum(probs)):.6f}")
        print()
        print("Goal predictions")
        print(f"- Expected home goals: {home_goal:.6f}")
        print(f"- Expected away goals: {away_goal:.6f}")
        print(f"- Total expected:      {home_goal + away_goal:.6f}")

        if not np.isclose(np.sum(probs), 1.0, atol=1e-5):
            raise RuntimeError("1X2 probabilities do not sum to ~1.0")
        if home_goal < 0 or away_goal < 0:
            raise RuntimeError("Goal predictions must be non-negative after clipping")

        print()
        print("✓ Retrained model bundles loaded and produced valid predictions")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
