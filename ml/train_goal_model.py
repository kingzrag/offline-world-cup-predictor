"""
Goal Predictor Model — Training Script
=======================================
Trains XGBoost regressors on dataset_goals.csv.

Output:
  - models/goal_predictor.pkl   (trained model + metadata bundle)
  - Metrics printed to stdout

Usage:
    python3 -m ml.train_goal_model
"""

import os
import sys
import pickle
import warnings
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split, KFold, cross_validate
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb
import scipy.stats

warnings.filterwarnings("ignore")

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ML_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(ML_DIR)
DATASET_PATH = os.path.join(ML_DIR, "dataset_goals.csv")
MODEL_DIR = os.path.join(PROJECT_ROOT, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "goal_predictor.pkl")

GOAL_FEATURES = [
    "elo_diff",
    "fifa_diff",
    "form_diff",
    "gs_diff",
    "gc_diff",
    "inj_diff",
    "susp_diff",
    "available_squad_diff",
    "availability_pct_diff",
    "starting_xi_value_diff",
    "missing_star_players_diff",
    "elo_momentum_diff",
    "home_elo_momentum",
    "away_elo_momentum",
    "strength_of_schedule_diff",
    "home_strength_of_schedule",
    "away_strength_of_schedule",
    "world_cup_matches_played_diff",
    "major_tournament_matches_diff",
    "knockout_matches_diff",
    "home_adv",
    "h2h_factor",
    "match_stage_weight",
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
    "home_injury_count",
    "away_injury_count",
    "home_suspension_count",
    "away_suspension_count",
    "home_injury_market_value_loss",
    "away_injury_market_value_loss",
    "mv_diff",
    # ---- NEW FEATURES! ----
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

HOME_TARGET = "home_score"
AWAY_TARGET = "away_score"


# ---------------------------------------------------------------------------
# Load & prepare data
# ---------------------------------------------------------------------------
def load_data():
    print(f"\n{'='*60}")
    print("  FEATURE LIST USED FOR GOAL MODEL TRAINING")
    print(f"{'='*60}")
    for i, f in enumerate(GOAL_FEATURES, 1):
        print(f"    {i:2d}. {f}")
    
    df = pd.read_csv(DATASET_PATH)
    
    # Drop rows where any feature or target column is missing
    before = len(df)
    cols_to_check = GOAL_FEATURES + [HOME_TARGET, AWAY_TARGET]
    df = df.dropna(subset=cols_to_check)
    after = len(df)
    
    if before != after:
        print(f"  ⚠ Dropped {before - after} rows with missing values")
        
    print(f"\n{'='*60}")
    print(f"  Dataset: {after} rows | {len(GOAL_FEATURES)} features")
    print(f"{'='*60}")
    print(f"  Goals Summary:")
    print(f"    Home Goals: mean = {df[HOME_TARGET].mean():.2f}, std = {df[HOME_TARGET].std():.2f}")
    print(f"    Away Goals: mean = {df[AWAY_TARGET].mean():.2f}, std = {df[AWAY_TARGET].std():.2f}")
    
    X = df[GOAL_FEATURES].values
    y_home = df[HOME_TARGET].values
    y_away = df[AWAY_TARGET].values
    return X, y_home, y_away


# ---------------------------------------------------------------------------
# Train
# ---------------------------------------------------------------------------
def train(X, y_home, y_away):
    # Split using column stack to keep alignments
    X_train, X_test, y_combined_train, y_combined_test = train_test_split(
        X, np.column_stack((y_home, y_away)), test_size=0.2, random_state=42
    )
    
    y_home_train = y_combined_train[:, 0]
    y_away_train = y_combined_train[:, 1]
    y_home_test = y_combined_test[:, 0]
    y_away_test = y_combined_test[:, 1]
    
    print(f"\n  Train: {len(X_train)} | Test: {len(X_test)}")

    model_params = {
        "n_estimators": 400,
        "max_depth": 5,
        "learning_rate": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "min_child_weight": 3,
        "reg_alpha": 0.1,
        "reg_lambda": 1.0,
        "objective": "reg:squarederror",
        "eval_metric": "rmse",
        "random_state": 42,
        "n_jobs": -1,
    }

    home_model = xgb.XGBRegressor(**model_params)
    away_model = xgb.XGBRegressor(**model_params)

    print("  Training Home Goals model ...")
    home_model.fit(
        X_train, y_home_train,
        eval_set=[(X_test, y_home_test)],
        verbose=False,
    )

    print("  Training Away Goals model ...")
    away_model.fit(
        X_train, y_away_train,
        eval_set=[(X_test, y_away_test)],
        verbose=False,
    )

    return home_model, away_model, X_train, X_test, y_home_train, y_home_test, y_away_train, y_away_test


# ---------------------------------------------------------------------------
# Evaluate
# ---------------------------------------------------------------------------
def evaluate(home_model, away_model, X_train, X_test, y_home_train, y_home_test, y_away_train, y_away_test, X_all, y_home_all, y_away_all):
    print(f"\n{'='*60}")
    print("  HOLD-OUT TEST SET METRICS")
    print(f"{'='*60}")
    
    # Evaluate Home Model
    y_home_pred = home_model.predict(X_test)
    home_mae = mean_absolute_error(y_home_test, y_home_pred)
    home_rmse = np.sqrt(mean_squared_error(y_home_test, y_home_pred))
    home_r2 = r2_score(y_home_test, y_home_pred)
    
    print("  [Home Goals Model]")
    print(f"    MAE  : {home_mae:.4f}")
    print(f"    RMSE : {home_rmse:.4f}")
    print(f"    R²   : {home_r2:.4f}")
    
    # Evaluate Away Model
    y_away_pred = away_model.predict(X_test)
    away_mae = mean_absolute_error(y_away_test, y_away_pred)
    away_rmse = np.sqrt(mean_squared_error(y_away_test, y_away_pred))
    away_r2 = r2_score(y_away_test, y_away_pred)
    
    print("\n  [Away Goals Model]")
    print(f"    MAE  : {away_mae:.4f}")
    print(f"    RMSE : {away_rmse:.4f}")
    print(f"    R²   : {away_r2:.4f}")
    
    # Cross Validation
    print(f"\n{'='*60}")
    print("  5-FOLD CROSS-VALIDATION (full dataset)")
    print(f"{'='*60}")
    
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    cv_params = {
        "n_estimators": 400, "max_depth": 5, "learning_rate": 0.05,
        "subsample": 0.8, "colsample_bytree": 0.8, "min_child_weight": 3,
        "reg_alpha": 0.1, "reg_lambda": 1.0,
        "objective": "reg:squarederror", "eval_metric": "rmse",
        "random_state": 42, "n_jobs": -1,
    }
    
    home_cv_model = xgb.XGBRegressor(**cv_params)
    away_cv_model = xgb.XGBRegressor(**cv_params)
    
    home_cv_results = cross_validate(
        home_cv_model, X_all, y_home_all, cv=cv,
        scoring=["neg_mean_absolute_error", "neg_root_mean_squared_error", "r2"],
        n_jobs=-1,
    )
    
    away_cv_results = cross_validate(
        away_cv_model, X_all, y_away_all, cv=cv,
        scoring=["neg_mean_absolute_error", "neg_root_mean_squared_error", "r2"],
        n_jobs=-1,
    )
    
    print("  Home CV MAE  : {:.4f} ± {:.4f}".format(-home_cv_results['test_neg_mean_absolute_error'].mean(), home_cv_results['test_neg_mean_absolute_error'].std()))
    print("  Home CV RMSE : {:.4f} ± {:.4f}".format(-home_cv_results['test_neg_root_mean_squared_error'].mean(), home_cv_results['test_neg_root_mean_squared_error'].std()))
    print("  Home CV R²   : {:.4f} ± {:.4f}".format(home_cv_results['test_r2'].mean(), home_cv_results['test_r2'].std()))
    
    print("\n  Away CV MAE  : {:.4f} ± {:.4f}".format(-away_cv_results['test_neg_mean_absolute_error'].mean(), away_cv_results['test_neg_mean_absolute_error'].std()))
    print("  Away CV RMSE : {:.4f} ± {:.4f}".format(-away_cv_results['test_neg_root_mean_squared_error'].mean(), away_cv_results['test_neg_root_mean_squared_error'].std()))
    print("  Away CV R²   : {:.4f} ± {:.4f}".format(away_cv_results['test_r2'].mean(), away_cv_results['test_r2'].std()))

    return {
        "home_mae": home_mae, "home_rmse": home_rmse, "home_r2": home_r2,
        "away_mae": away_mae, "away_rmse": away_rmse, "away_r2": away_r2
    }


# ---------------------------------------------------------------------------
# Feature importance
# ---------------------------------------------------------------------------
def print_feature_importance(home_model, away_model):
    print(f"\n{'='*60}")
    print("  FEATURE IMPORTANCE (Gain) - HOME / AWAY MODELS")
    print(f"{'='*60}")
    home_imp = home_model.feature_importances_
    away_imp = away_model.feature_importances_
    
    ranked_home = sorted(zip(GOAL_FEATURES, home_imp), key=lambda x: x[1], reverse=True)
    ranked_away = sorted(zip(GOAL_FEATURES, away_imp), key=lambda x: x[1], reverse=True)
    
    print("  [Home Goals Model]")
    for i, (feat, imp) in enumerate(ranked_home[:10], 1):
        bar = "█" * int(imp * 100)
        print(f"    {i:2d}. {feat:25s} {imp:.4f}  {bar}")
        
    print("\n  [Away Goals Model]")
    for i, (feat, imp) in enumerate(ranked_away[:10], 1):
        bar = "█" * int(imp * 100)
        print(f"    {i:2d}. {feat:25s} {imp:.4f}  {bar}")


# ---------------------------------------------------------------------------
# Save model bundle
# ---------------------------------------------------------------------------
def save_model(home_model, away_model, metrics):
    os.makedirs(MODEL_DIR, exist_ok=True)
    bundle = {
        "home_model": home_model,
        "away_model": away_model,
        "features": GOAL_FEATURES,
        "metrics": metrics,
        "version": "1.0",
    }
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(bundle, f)
    size_kb = os.path.getsize(MODEL_PATH) / 1024
    print(f"\n  ✅ Goal Predictor Model saved → {MODEL_PATH}  ({size_kb:.1f} KB)")


# ---------------------------------------------------------------------------
# Prediction function
# ---------------------------------------------------------------------------
def predict_goals(home_team: str, away_team: str, db=None) -> dict:
    """
    Predict goals and derived betting markets for home_team and away_team.

    Args:
        home_team: Name of the home team (e.g. "Brazil")
        away_team: Name of the away team (e.g. "Germany")
        db: Optional SQLAlchemy session. If None, a new session is opened.

    Returns:
        A dict matching the required predictions output schema.
    """
    from database.connection import SessionLocal
    from models import Team
    from ml.features import extract_ml_features
    from datetime import datetime, timezone

    # Resolve model bundle path
    current_ml_dir = os.path.dirname(os.path.abspath(__file__))
    current_proj_root = os.path.dirname(current_ml_dir)
    current_model_path = os.path.join(current_proj_root, "models", "goal_predictor.pkl")

    with open(current_model_path, "rb") as f:
        bundle = pickle.load(f)

    home_model = bundle["home_model"]
    away_model = bundle["away_model"]
    features_list = bundle["features"]

    close_db = db is None
    if db is None:
        db = SessionLocal()

    try:
        home = db.query(Team).filter(Team.name == home_team, Team.gender == "MEN").first()
        away = db.query(Team).filter(Team.name == away_team, Team.gender == "MEN").first()

        if not home:
            raise ValueError(f"Team not found: '{home_team}'")
        if not away:
            raise ValueError(f"Team not found: '{away_team}'")

        now = datetime.now(timezone.utc)

        # Extract features (uses WC neutral context and None stage weight as default)
        feat_dict = extract_ml_features(
            db, home.id, away.id, now,
            competition_code="WC",
            match_stage=None,
        )

        # Build feature vector in exact training order
        feature_vec = np.array([[feat_dict.get(f, 0.0) for f in features_list]])

        # Predict raw expected goals
        pred_home = float(home_model.predict(feature_vec)[0])
        pred_away = float(away_model.predict(feature_vec)[0])

        # Clip predictions at 0
        expected_home_goals = max(0.0, pred_home)
        expected_away_goals = max(0.0, pred_away)
        total_expected_goals = expected_home_goals + expected_away_goals

        # ----------------------------------------------------
        # Derived Market Calculations via Poisson Probability Engine
        # ----------------------------------------------------
        from services.poisson_engine import evaluate_poisson_engine

        poisson_res = evaluate_poisson_engine(expected_home_goals, expected_away_goals)

        # Backward-compatible mappings
        over_1_5 = poisson_res["over_under"]["1.5"]["over"]
        under_1_5 = poisson_res["over_under"]["1.5"]["under"]
        over_2_5 = poisson_res["over_under"]["2.5"]["over"]
        under_2_5 = poisson_res["over_under"]["2.5"]["under"]
        over_3_5 = poisson_res["over_under"]["3.5"]["over"]
        under_3_5 = poisson_res["over_under"]["3.5"]["under"]

        btts_yes = poisson_res["btts"]["btts_yes"]
        btts_no = poisson_res["btts"]["btts_no"]
        best_score = poisson_res["most_likely_score"]

        # Asian Handicap simple string format
        diff = expected_home_goals - expected_away_goals
        if diff > 1.5:
            asian_handicap = "Home -1.5"
        elif diff > 0.5:
            asian_handicap = "Home -0.5"
        elif diff > -0.5:
            asian_handicap = "Level (0)"
        elif diff > -1.5:
            asian_handicap = "Away -0.5"
        else:
            asian_handicap = "Away -1.5"

        home_team_goal_line = round(expected_home_goals * 2) / 2
        away_team_goal_line = round(expected_away_goals * 2) / 2

        return {
            "expected_home_goals":   round(expected_home_goals, 4),
            "expected_away_goals":   round(expected_away_goals, 4),
            "total_expected_goals":  round(total_expected_goals, 4),
            "over_2_5_probability":  round(over_2_5, 4),
            "under_2_5_probability": round(under_2_5, 4),
            "over_1_5_probability":  round(over_1_5, 4),
            "under_1_5_probability": round(under_1_5, 4),
            "over_3_5_probability":  round(over_3_5, 4),
            "under_3_5_probability": round(under_3_5, 4),
            "btts_yes_probability":  round(btts_yes, 4),
            "btts_no_probability":   round(btts_no, 4),
            "most_likely_score":     best_score,
            "asian_handicap":        asian_handicap,
            "home_team_goal_line":   float(home_team_goal_line),
            "away_team_goal_line":   float(away_team_goal_line),

            # --- Phase 4.5 Advanced Goal Intelligence markets ---
            "probability_matrix":    poisson_res["probability_matrix"],
            "top_5_scorelines":      poisson_res["top_5_scorelines"],
            "btts_yes_percentage":   round(btts_yes * 100, 2),
            "btts_no_percentage":    round(btts_no * 100, 2),
            "over_1_5_percentage":   round(over_1_5 * 100, 2),
            "under_1_5_percentage":  round(under_1_5 * 100, 2),
            "over_2_5_percentage":   round(over_2_5 * 100, 2),
            "under_2_5_percentage":  round(under_2_5 * 100, 2),
            "over_3_5_percentage":   round(over_3_5 * 100, 2),
            "under_3_5_percentage":  round(under_3_5 * 100, 2),
            "asian_handicap_probabilities": poisson_res["asian_handicap"]["suggested_lines"],
            "team_goals_probabilities": poisson_res["team_goals"]
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
    print("  SAMPLE PREDICTIONS (Goal Model & Markets)")
    print(f"{'='*60}")
    for home, away in fixtures:
        try:
            res = predict_goals(home, away)
            print(f"\n  {home:20s} vs {away}")
            print(f"    Exp Goals       : Home {res['expected_home_goals']:.2f} | Away {res['expected_away_goals']:.2f} (Total {res['total_expected_goals']:.2f})")
            print(f"    Over/Under 2.5  : Over {res['over_2_5_probability']*100:.1f}% | Under {res['under_2_5_probability']*100:.1f}%")
            print(f"    BTTS Yes / No   : Yes {res['btts_yes_probability']*100:.1f}% | No {res['btts_no_probability']*100:.1f}%")
            print(f"    Most Likely     : {res['most_likely_score']}")
            print(f"    Asian Handicap  : {res['asian_handicap']}")
            print(f"    Goal Lines      : Home {res['home_team_goal_line']:.1f} | Away {res['away_team_goal_line']:.1f}")
        except Exception as e:
            print(f"  ⚠ {home} vs {away}: {e}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("\n  Goal Predictor Model — Training starting ...")
    X, y_home, y_away = load_data()
    
    (home_model, away_model, X_train, X_test, 
     y_home_train, y_home_test, y_away_train, y_away_test) = train(X, y_home, y_away)
    
    metrics = evaluate(
        home_model, away_model, 
        X_train, X_test, 
        y_home_train, y_home_test, 
        y_away_train, y_away_test, 
        X, y_home, y_away
    )
    
    print_feature_importance(home_model, away_model)
    save_model(home_model, away_model, metrics)
    print_sample_predictions()
    
    print(f"\n{'='*60}")
    print("  Goal model training complete.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
