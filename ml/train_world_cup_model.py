"""
World Cup Match Predictor — Training Script
==========================================
Trains an XGBoost classifier on dataset_world_cup.csv.

Output:
  - models/world_cup_predictor.pkl   (trained model + metadata bundle)
  - Metrics printed to stdout

Usage:
    python3 -m ml.train_world_cup_model
"""

import os
import sys
import pickle
import warnings
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score,
    log_loss,
    f1_score,
    confusion_matrix,
    classification_report,
)
import xgboost as xgb

warnings.filterwarnings("ignore")

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ML_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(ML_DIR)
DATASET_PATH = os.path.join(ML_DIR, "dataset_world_cup.csv")
MODEL_DIR = os.path.join(PROJECT_ROOT, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "world_cup_predictor.pkl")

FEATURES = [
    # Phase 1 core
    "elo_diff",
    "fifa_diff",
    "form_diff",
    "gs_diff",
    "gc_diff",
    "inj_diff",
    "susp_diff",
    "home_adv",
    "h2h_factor",
    # Phase 2 player intelligence
    "available_squad_diff",
    "starting_xi_value_diff",
    "missing_star_players_diff",
    "match_stage_weight",
    # Phase 3 structural
    "elo_momentum_diff",
    "home_elo_momentum",
    "away_elo_momentum",
    "strength_of_schedule_diff",
    "home_strength_of_schedule",
    "away_strength_of_schedule",
    "world_cup_matches_played_diff",
    "major_tournament_matches_diff",
    "knockout_matches_diff",
    # Injury & Suspension counts & absolute market-value loss
    "home_injury_count",
    "away_injury_count",
    "home_suspension_count",
    "away_suspension_count",
    "home_injury_market_value_loss",
    "away_injury_market_value_loss",
    # Phase 4.5 Advanced Goal Intelligence
    "home_attack_rating",
    "away_attack_rating",
    "attack_rating_diff",
    "home_defence_rating",
    "away_defence_rating",
    "defence_rating_diff",
    "home_clean_sheet_rate",
    "away_clean_sheet_rate",
    "clean_sheet_rate_diff",
    "home_btts_rate",
    "away_btts_rate",
    "btts_rate_diff",
    "mv_diff",
    # ---- NEW FEATURES (Standings, Odds, Live)! ----
    "home_group_position",
    "away_group_position",
    "group_position_diff",
    "home_points",
    "away_points",
    "points_diff",
    "goal_difference_diff",
    "home_implied_probability",
    "draw_implied_probability",
    "away_implied_probability",
    "current_minute",
    "time_remaining",
    "current_score_diff",
    "home_red_cards",
    "away_red_cards",
    "red_card_diff",
]
TARGET = "target"

LABEL_MAP = {0: "Away Win", 1: "Draw", 2: "Home Win"}


# ---------------------------------------------------------------------------
# Load & prepare data
# ---------------------------------------------------------------------------
def load_data():
    print(f"\n{'='*60}")
    print("  FEATURE LIST USED FOR TRAINING")
    print(f"{'='*60}")
    for i, f in enumerate(FEATURES, 1):
        print(f"    {i:2d}. {f}")
    df = pd.read_csv(DATASET_PATH)
    # Drop rows where any feature column is missing
    before = len(df)
    df = df.dropna(subset=FEATURES)
    after = len(df)
    if before != after:
        print(f"  ⚠ Dropped {before - after} rows with missing feature values")
    print(f"\n{'='*60}")
    print(f"  Dataset: {after} rows | {len(FEATURES)} features")
    print(f"{'='*60}")
    print(f"  Target distribution:")
    vc = df[TARGET].value_counts().sort_index()
    for k, v in vc.items():
        print(f"    {LABEL_MAP[k]:10s}: {v:5d} ({100*v/len(df):.1f}%)")
    X = df[FEATURES].values
    y = df[TARGET].values
    return X, y


# ---------------------------------------------------------------------------
# Train
# ---------------------------------------------------------------------------
def train(X, y):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\n  Train: {len(X_train)} | Test: {len(X_test)}")

    model = xgb.XGBClassifier(
        n_estimators=400,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        gamma=0.1,
        reg_alpha=0.1,
        reg_lambda=1.0,
        objective="multi:softprob",
        num_class=3,
        eval_metric="mlogloss",
        random_state=42,
        n_jobs=-1,
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )

    return model, X_train, X_test, y_train, y_test


# ---------------------------------------------------------------------------
# Evaluate
# ---------------------------------------------------------------------------
def evaluate(model, X_train, X_test, y_train, y_test, X_all, y_all):
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)

    acc = accuracy_score(y_test, y_pred)
    ll = log_loss(y_test, y_prob)
    f1_macro = f1_score(y_test, y_pred, average="macro")
    f1_weighted = f1_score(y_test, y_pred, average="weighted")
    cm = confusion_matrix(y_test, y_pred)

    print(f"\n{'='*60}")
    print("  HOLD-OUT TEST SET METRICS")
    print(f"{'='*60}")
    print(f"  Accuracy       : {acc:.4f}  ({acc*100:.2f}%)")
    print(f"  Log Loss       : {ll:.4f}")
    print(f"  F1 Macro       : {f1_macro:.4f}")
    print(f"  F1 Weighted    : {f1_weighted:.4f}")

    print(f"\n  Confusion Matrix (rows=actual, cols=predicted):")
    print(f"                 Pred Away  Pred Draw  Pred Home")
    labels = ["Away Win", "Draw    ", "Home Win"]
    for i, row in enumerate(cm):
        print(f"  Actual {labels[i]}: {row[0]:8d}   {row[1]:8d}   {row[2]:8d}")

    print(f"\n  Per-class report:")
    print(classification_report(
        y_test, y_pred,
        target_names=["Away Win", "Draw", "Home Win"],
        digits=4
    ))

    # 5-fold cross-validation
    print(f"{'='*60}")
    print("  5-FOLD CROSS-VALIDATION (full dataset)")
    print(f"{'='*60}")
    cv_model = xgb.XGBClassifier(
        n_estimators=400, max_depth=5, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
        gamma=0.1, reg_alpha=0.1, reg_lambda=1.0,
        objective="multi:softprob", num_class=3,
        eval_metric="mlogloss",
        random_state=42, n_jobs=-1,
    )
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_results = cross_validate(
        cv_model, X_all, y_all, cv=cv,
        scoring=["accuracy", "neg_log_loss", "f1_macro"],
        n_jobs=-1,
    )
    print(f"  CV Accuracy   : {cv_results['test_accuracy'].mean():.4f} ± {cv_results['test_accuracy'].std():.4f}")
    print(f"  CV Log Loss   : {-cv_results['test_neg_log_loss'].mean():.4f} ± {cv_results['test_neg_log_loss'].std():.4f}")
    print(f"  CV F1 Macro   : {cv_results['test_f1_macro'].mean():.4f} ± {cv_results['test_f1_macro'].std():.4f}")

    return acc, ll, f1_macro


# ---------------------------------------------------------------------------
# Feature importance
# ---------------------------------------------------------------------------
def print_feature_importance(model):
    print(f"\n{'='*60}")
    print("  FEATURE IMPORTANCE (gain)")
    print(f"{'='*60}")
    importances = model.feature_importances_
    ranked = sorted(zip(FEATURES, importances), key=lambda x: x[1], reverse=True)
    for i, (feat, imp) in enumerate(ranked, 1):
        bar = "█" * int(imp * 200)
        print(f"  {i}. {feat:15s} {imp:.4f}  {bar}")


# ---------------------------------------------------------------------------
# Save model bundle
# ---------------------------------------------------------------------------
def save_model(model, acc, ll, f1):
    os.makedirs(MODEL_DIR, exist_ok=True)
    bundle = {
        "model": model,
        "features": FEATURES,
        "label_map": LABEL_MAP,
        "label_encoder": None,  # not needed — targets are already 0/1/2
        "metrics": {"accuracy": acc, "log_loss": ll, "f1_macro": f1},
        "version": "1.0",
    }
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(bundle, f)
    size_kb = os.path.getsize(MODEL_PATH) / 1024
    print(f"\n  ✅ Model saved → {MODEL_PATH}  ({size_kb:.1f} KB)")


# ---------------------------------------------------------------------------
# Prediction function
# ---------------------------------------------------------------------------
def predict_match(home_team: str, away_team: str, db=None) -> dict:
    """
    Predict the outcome of a match between home_team and away_team.

    Args:
        home_team: Name of the home team (e.g. "Brazil")
        away_team: Name of the away team (e.g. "Germany")
        db: Optional SQLAlchemy session. If None, a new session is opened.

    Returns:
        {
          "home_win_probability": float,
          "draw_probability": float,
          "away_win_probability": float,
          "predicted_result": str,
          "confidence": str   # "Low" | "Medium" | "High"
        }
    """
    from database.connection import SessionLocal
    from models import Team
    from ml.features import extract_ml_features
    from datetime import datetime, timezone

    with open(MODEL_PATH, "rb") as f:
        bundle = pickle.load(f)

    model   = bundle["model"]
    features_list = bundle["features"]
    label_map     = bundle["label_map"]

    close_db = db is None
    if db is None:
        db = SessionLocal()

    try:
        home = db.query(Team).filter(Team.name == home_team).first()
        away = db.query(Team).filter(Team.name == away_team).first()

        if not home:
            raise ValueError(f"Team not found: '{home_team}'")
        if not away:
            raise ValueError(f"Team not found: '{away_team}'")

        now = datetime.now(timezone.utc)

        # Use shared feature extraction (covers Phase 1, 2 and 3)
        feat_dict = extract_ml_features(
            db, home.id, away.id, now,
            competition_code="WC",  # neutral international context
            match_stage=None,       # unknown future stage → weight 0
        )

        # Build feature vector in the exact order the model was trained on
        feature_vec = np.array([[feat_dict.get(f, 0.0) for f in features_list]])

        probs = model.predict_proba(feature_vec)[0]  # [away_win, draw, home_win]
        predicted_class = int(np.argmax(probs))
        predicted_label = label_map[predicted_class]

        # Confidence: spread between top and second probability
        sorted_probs = sorted(probs, reverse=True)
        diff = sorted_probs[0] - sorted_probs[1]
        if diff >= 0.25:
            confidence = "High"
        elif diff >= 0.10:
            confidence = "Medium"
        else:
            confidence = "Low"

        return {
            "home_win_probability":  round(float(probs[2]), 4),
            "draw_probability":      round(float(probs[1]), 4),
            "away_win_probability":  round(float(probs[0]), 4),
            "predicted_result":      predicted_label,
            "confidence":            confidence,
        }
    finally:
        if close_db:
            db.close()


# ---------------------------------------------------------------------------
# Sample predictions
# ---------------------------------------------------------------------------
def print_sample_predictions():
    fixtures = [
        ("Brazil",   "Germany"),
        ("Argentina", "Spain"),
        ("France",   "England"),
        ("Portugal", "Netherlands"),
        ("Morocco",  "Senegal"),
    ]
    print(f"\n{'='*60}")
    print("  SAMPLE PREDICTIONS (with confidence)")
    print(f"{'='*60}")
    for home, away in fixtures:
        try:
            result = predict_match(home, away)
            print(f"\n  {home:20s} vs {away}")
            print(f"    Home Win : {result['home_win_probability']*100:5.1f}%")
            print(f"    Draw     : {result['draw_probability']*100:5.1f}%")
            print(f"    Away Win : {result['away_win_probability']*100:5.1f}%")
            print(f"    → Predicted : {result['predicted_result']}")
            print(f"    → Confidence: {result['confidence']}")
        except Exception as e:
            print(f"  ⚠ {home} vs {away}: {e}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("\n  World Cup Predictor — Training")
    X, y = load_data()
    model, X_train, X_test, y_train, y_test = train(X, y)
    acc, ll, f1 = evaluate(model, X_train, X_test, y_train, y_test, X, y)
    print_feature_importance(model)
    save_model(model, acc, ll, f1)
    print_sample_predictions()
    print(f"\n{'='*60}")
    print("  Training complete.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
