"""
ml/train_club_models_v2.py

STEP 6C — Train, Evaluate, and Shadow-Test ML Models for Club Football.

Features Trained:
1. Outcome Model (1X2): XGBClassifier (0=Away Win, 1=Draw, 2=Home Win)
2. Goal Models (xG): Home & Away XGBRegressors
3. Clean Sheet Model: XGBClassifier (Binary 0/1)
4. Asian Handicap Model: XGBClassifier (Binary 0/1 cover for -0.5 AH)

Variants Trained:
- Variant A: Club-Only (ml/dataset_club_leagues.csv)
- Variant B: Club + International (Harmonized features)

Safety Constraints:
- NEVER overwrites existing models (saves with '_v2.pkl' suffix)
- Uses strict chronological train/test split (80% train / 20% test per league)
- Evaluates per competition (PL, PD, SA, BL1, FL1, DED, BSA)
"""

import os
import json
import pickle
import logging
import datetime
import numpy as np
import pandas as pd
import xgboost as xgb

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    log_loss,
    brier_score_loss,
    mean_absolute_error,
    root_mean_squared_error,
    precision_score,
    recall_score,
    confusion_matrix,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")
logger = logging.getLogger("train_v2")

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MODELS_DIR = os.path.join(_ROOT, "models")
_DATASET_CLUB = os.path.join(_ROOT, "ml", "dataset_club_leagues.csv")
_DATASET_INTL = os.path.join(_ROOT, "ml", "dataset_international_retrain.csv")

# Clean, leakage-safe features for Club training
CLUB_FEATURES = [
    "elo_diff",
    "form_diff",
    "gs_diff",
    "gc_diff",
    "home_adv",
    "h2h_factor",
    "home_elo_momentum",
    "away_elo_momentum",
    "elo_momentum_diff",
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
    "home_recent_form",
    "away_recent_form",
    "recent_form_diff",
]


def load_club_dataset() -> pd.DataFrame:
    if not os.path.exists(_DATASET_CLUB):
        raise FileNotFoundError(f"Club dataset not found at {_DATASET_CLUB}")
    df = pd.read_csv(_DATASET_CLUB)
    df["utc_date"] = pd.to_datetime(df["utc_date"])
    df = df.sort_values("utc_date").reset_index(drop=True)
    return df


def load_harmonized_combined_dataset() -> pd.DataFrame:
    df_club = load_club_dataset()
    if not os.path.exists(_DATASET_INTL):
        logger.warning("Intl dataset not found, returning club only")
        return df_club

    df_intl = pd.read_csv(_DATASET_INTL)
    df_intl["utc_date"] = pd.to_datetime(df_intl["utc_date"])

    # Harmonize recent_form to PPG scale (0..3) if it was on win-rate scale (0..1)
    if df_intl["home_recent_form"].max() <= 1.0:
        df_intl["home_recent_form"] = df_intl["home_recent_form"] * 3.0
        df_intl["away_recent_form"] = df_intl["away_recent_form"] * 3.0
        df_intl["recent_form_diff"] = df_intl["home_recent_form"] - df_intl["away_recent_form"]

    # Select common features
    keep_cols = ["utc_date", "competition_code", "target", "home_score", "away_score", "home_clean_sheet", "away_clean_sheet", "btts", "ah_cover"] + CLUB_FEATURES
    
    # Fill missing columns in intl if any
    for col in keep_cols:
        if col not in df_intl.columns:
            if col == "home_clean_sheet":
                df_intl["home_clean_sheet"] = (df_intl["away_score"] == 0).astype(int)
            elif col == "away_clean_sheet":
                df_intl["away_clean_sheet"] = (df_intl["home_score"] == 0).astype(int)
            elif col == "btts":
                df_intl["btts"] = ((df_intl["home_score"] > 0) & (df_intl["away_score"] > 0)).astype(int)
            elif col == "ah_cover":
                df_intl["ah_cover"] = ((df_intl["home_score"] - df_intl["away_score"]) > 0).astype(int)
            else:
                df_intl[col] = 0.0

    df_c_sub = df_club[keep_cols].copy()
    df_i_sub = df_intl[keep_cols].copy()

    df_combined = pd.concat([df_c_sub, df_i_sub], ignore_index=True)
    df_combined = df_combined.sort_values("utc_date").reset_index(drop=True)
    return df_combined


def chronological_split(df: pd.DataFrame, train_ratio: float = 0.8) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Splits each competition chronologically (80% train, 20% test)."""
    train_dfs = []
    test_dfs = []
    split_info = {}

    for comp in df["competition_code"].unique():
        comp_df = df[df["competition_code"] == comp].sort_values("utc_date").reset_index(drop=True)
        n = len(comp_df)
        n_train = int(n * train_ratio)
        
        train_sub = comp_df.iloc[:n_train]
        test_sub = comp_df.iloc[n_train:]

        train_dfs.append(train_sub)
        test_dfs.append(test_sub)

        split_info[comp] = {
            "total": n,
            "train_n": len(train_sub),
            "test_n": len(test_sub),
            "train_max_date": str(train_sub["utc_date"].max())[:10] if len(train_sub) > 0 else "N/A",
            "test_min_date": str(test_sub["utc_date"].min())[:10] if len(test_sub) > 0 else "N/A",
            "test_max_date": str(test_sub["utc_date"].max())[:10] if len(test_sub) > 0 else "N/A",
        }

    train_df = pd.concat(train_dfs, ignore_index=True).sort_values("utc_date").reset_index(drop=True)
    test_df = pd.concat(test_dfs, ignore_index=True).sort_values("utc_date").reset_index(drop=True)

    return train_df, test_df, split_info


def train_and_evaluate_variant(variant_name: str, df: pd.DataFrame) -> dict:
    logger.info(f"\n=======================================================")
    logger.info(f" TRAINING VARIANT: {variant_name}")
    logger.info(f" Total rows: {len(df)}")
    logger.info(f"=======================================================")

    train_df, test_df, split_info = chronological_split(df, train_ratio=0.8)
    logger.info(f"Train rows: {len(train_df)} | Test rows: {len(test_df)}")

    X_train = train_df[CLUB_FEATURES]
    X_test = test_df[CLUB_FEATURES]

    # --------------------------------------------------------------------------
    # 1. OUTCOME MODEL (1X2)
    # Target mapping: 0 = Away Win, 1 = Draw, 2 = Home Win
    # --------------------------------------------------------------------------
    y_train_1x2 = train_df["target"]
    y_test_1x2 = test_df["target"]

    clf_1x2 = xgb.XGBClassifier(
        n_estimators=150,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric="mlogloss",
    )
    clf_1x2.fit(X_train, y_train_1x2)

    probs_1x2 = clf_1x2.predict_proba(X_test)
    preds_1x2 = clf_1x2.predict(X_test)

    acc_1x2 = accuracy_score(y_test_1x2, preds_1x2)
    bal_acc_1x2 = balanced_accuracy_score(y_test_1x2, preds_1x2)
    f1_1x2 = f1_score(y_test_1x2, preds_1x2, average="macro")
    ll_1x2 = log_loss(y_test_1x2, probs_1x2)
    
    # One-hot for brier score
    y_test_oh = pd.get_dummies(y_test_1x2).values
    brier_1x2 = np.mean(np.sum((probs_1x2 - y_test_oh) ** 2, axis=1))

    cm_1x2 = confusion_matrix(y_test_1x2, preds_1x2).tolist()

    # Per-league 1X2 metrics
    league_1x2 = {}
    for comp in test_df["competition_code"].unique():
        idx = test_df["competition_code"] == comp
        if idx.sum() == 0: continue
        sub_y = y_test_1x2[idx]
        sub_pred = preds_1x2[idx]
        sub_prob = probs_1x2[idx]
        league_1x2[comp] = {
            "n": int(idx.sum()),
            "accuracy": round(float(accuracy_score(sub_y, sub_pred)), 4),
            "balanced_accuracy": round(float(balanced_accuracy_score(sub_y, sub_pred)), 4),
            "f1": round(float(f1_score(sub_y, sub_pred, average="macro")), 4),
            "log_loss": round(float(log_loss(sub_y, sub_prob, labels=[0,1,2])), 4),
        }

    # --------------------------------------------------------------------------
    # 2. GOAL MODELS (Home & Away xG)
    # --------------------------------------------------------------------------
    reg_home = xgb.XGBRegressor(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=42)
    reg_away = xgb.XGBRegressor(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=42)

    reg_home.fit(X_train, train_df["home_score"])
    reg_away.fit(X_train, train_df["away_score"])

    pred_home_goals = np.clip(reg_home.predict(X_test), 0, None)
    pred_away_goals = np.clip(reg_away.predict(X_test), 0, None)

    mae_home = mean_absolute_error(test_df["home_score"], pred_home_goals)
    rmse_home = root_mean_squared_error(test_df["home_score"], pred_home_goals)
    mae_away = mean_absolute_error(test_df["away_score"], pred_away_goals)
    rmse_away = root_mean_squared_error(test_df["away_score"], pred_away_goals)

    league_goals = {}
    for comp in test_df["competition_code"].unique():
        idx = test_df["competition_code"] == comp
        if idx.sum() == 0: continue
        sub_df = test_df[idx]
        sub_ph = pred_home_goals[idx]
        sub_pa = pred_away_goals[idx]
        league_goals[comp] = {
            "home_mae": round(float(mean_absolute_error(sub_df["home_score"], sub_ph)), 4),
            "home_rmse": round(float(root_mean_squared_error(sub_df["home_score"], sub_ph)), 4),
            "away_mae": round(float(mean_absolute_error(sub_df["away_score"], sub_pa)), 4),
            "away_rmse": round(float(root_mean_squared_error(sub_df["away_score"], sub_pa)), 4),
        }

    # --------------------------------------------------------------------------
    # 3. CLEAN SHEET MODEL (Home clean sheet)
    # --------------------------------------------------------------------------
    clf_cs = xgb.XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=42)
    clf_cs.fit(X_train, train_df["home_clean_sheet"])
    probs_cs = clf_cs.predict_proba(X_test)[:, 1]
    preds_cs = clf_cs.predict(X_test)

    acc_cs = accuracy_score(test_df["home_clean_sheet"], preds_cs)
    prec_cs = precision_score(test_df["home_clean_sheet"], preds_cs, zero_division=0)
    rec_cs = recall_score(test_df["home_clean_sheet"], preds_cs, zero_division=0)
    f1_cs = f1_score(test_df["home_clean_sheet"], preds_cs, zero_division=0)

    # --------------------------------------------------------------------------
    # 4. ASIAN HANDICAP MODEL
    # --------------------------------------------------------------------------
    clf_ah = xgb.XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=42)
    clf_ah.fit(X_train, train_df["ah_cover"])
    probs_ah = clf_ah.predict_proba(X_test)[:, 1]
    preds_ah = clf_ah.predict(X_test)

    acc_ah = accuracy_score(test_df["ah_cover"], preds_ah)
    prec_ah = precision_score(test_df["ah_cover"], preds_ah, zero_division=0)
    rec_ah = recall_score(test_df["ah_cover"], preds_ah, zero_division=0)
    f1_ah = f1_score(test_df["ah_cover"], preds_ah, zero_division=0)

    # Save model bundles (with '_v2.pkl' suffix)
    if variant_name == "variant_a_club":
        wc_bundle_v2 = {
            "model": clf_1x2,
            "features": CLUB_FEATURES,
            "version": "2.0-club",
            "training_date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "competitions": list(split_info.keys()),
            "metrics": {
                "accuracy": round(float(acc_1x2), 4),
                "balanced_accuracy": round(float(bal_acc_1x2), 4),
                "macro_f1": round(float(f1_1x2), 4),
                "log_loss": round(float(ll_1x2), 4),
                "brier_score": round(float(brier_1x2), 4),
            },
        }
        with open(os.path.join(_MODELS_DIR, "outcome_predictor_v2.pkl"), "wb") as f:
            pickle.dump(wc_bundle_v2, f)

        goal_bundle_v2 = {
            "home_model": reg_home,
            "away_model": reg_away,
            "features": CLUB_FEATURES,
            "version": "2.0-club",
            "training_date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "metrics": {
                "home_mae": round(float(mae_home), 4),
                "away_mae": round(float(mae_away), 4),
            },
        }
        with open(os.path.join(_MODELS_DIR, "goal_predictor_v2.pkl"), "wb") as f:
            pickle.dump(goal_bundle_v2, f)

        cs_bundle_v2 = {
            "model": clf_cs,
            "features": CLUB_FEATURES,
            "version": "2.0-club",
            "market_name": "clean_sheet",
        }
        with open(os.path.join(_MODELS_DIR, "clean_sheet_predictor_v2.pkl"), "wb") as f:
            pickle.dump(cs_bundle_v2, f)

        ah_bundle_v2 = {
            "model": clf_ah,
            "features": CLUB_FEATURES,
            "version": "2.0-club",
            "market_name": "asian_handicap",
        }
        with open(os.path.join(_MODELS_DIR, "asian_handicap_predictor_v2.pkl"), "wb") as f:
            pickle.dump(ah_bundle_v2, f)

    return {
        "variant": variant_name,
        "split_info": split_info,
        "1x2_metrics": {
            "accuracy": round(float(acc_1x2), 4),
            "balanced_accuracy": round(float(bal_acc_1x2), 4),
            "macro_f1": round(float(f1_1x2), 4),
            "log_loss": round(float(ll_1x2), 4),
            "brier_score": round(float(brier_1x2), 4),
            "confusion_matrix": cm_1x2,
            "per_league": league_1x2,
        },
        "goal_metrics": {
            "home_mae": round(float(mae_home), 4),
            "home_rmse": round(float(rmse_home), 4),
            "away_mae": round(float(mae_away), 4),
            "away_rmse": round(float(rmse_away), 4),
            "per_league": league_goals,
        },
        "clean_sheet_metrics": {
            "accuracy": round(float(acc_cs), 4),
            "precision": round(float(prec_cs), 4),
            "recall": round(float(rec_cs), 4),
            "f1": round(float(f1_cs), 4),
        },
        "asian_handicap_metrics": {
            "accuracy": round(float(acc_ah), 4),
            "precision": round(float(prec_ah), 4),
            "recall": round(float(rec_ah), 4),
            "f1": round(float(f1_ah), 4),
        },
        "models": {
            "clf_1x2": clf_1x2,
            "reg_home": reg_home,
            "reg_away": reg_away,
        }
    }


def evaluate_old_models_on_club_test(test_df: pd.DataFrame) -> dict:
    """Evaluates the OLD (current) model binaries on the club test set."""
    wc_path = os.path.join(_MODELS_DIR, "world_cup_predictor.pkl")
    goal_path = os.path.join(_MODELS_DIR, "goal_predictor.pkl")

    if not os.path.exists(wc_path) or not os.path.exists(goal_path):
        return {"error": "Old models not found"}

    with open(wc_path, "rb") as f:
        wc_bundle = pickle.load(f)
    with open(goal_path, "rb") as f:
        goal_bundle = pickle.load(f)

    wc_features = wc_bundle.get("features", [])
    wc_model = wc_bundle["model"]
    home_reg = goal_bundle["home_model"]
    away_reg = goal_bundle["away_model"]

    # Construct input matrix for old models (padding missing features with 0.0)
    X_old = []
    for _, row in test_df.iterrows():
        vec = [row.get(f, 0.0) for f in wc_features]
        X_old.append(vec)
    X_old = pd.DataFrame(X_old, columns=wc_features)

    # 1X2 Evaluation
    probs_1x2 = wc_model.predict_proba(X_old)
    preds_1x2 = wc_model.predict(X_old)
    y_test_1x2 = test_df["target"]

    acc = accuracy_score(y_test_1x2, preds_1x2)
    bal_acc = balanced_accuracy_score(y_test_1x2, preds_1x2)
    f1 = f1_score(y_test_1x2, preds_1x2, average="macro")
    ll = log_loss(y_test_1x2, probs_1x2)
    
    y_test_oh = pd.get_dummies(y_test_1x2).values
    brier = np.mean(np.sum((probs_1x2 - y_test_oh) ** 2, axis=1))

    # Goal evaluation
    goal_feats = goal_bundle.get("features", [])
    X_goal = []
    for _, row in test_df.iterrows():
        vec = [row.get(f, 0.0) for f in goal_feats]
        X_goal.append(vec)
    X_goal = pd.DataFrame(X_goal, columns=goal_feats)

    pred_h_goals = np.clip(home_reg.predict(X_goal), 0, None)
    pred_a_goals = np.clip(away_reg.predict(X_goal), 0, None)

    mae_h = mean_absolute_error(test_df["home_score"], pred_h_goals)
    rmse_h = root_mean_squared_error(test_df["home_score"], pred_h_goals)
    mae_a = mean_absolute_error(test_df["away_score"], pred_a_goals)
    rmse_a = root_mean_squared_error(test_df["away_score"], pred_a_goals)

    # Per-league 1X2
    league_1x2 = {}
    for comp in test_df["competition_code"].unique():
        idx = test_df["competition_code"] == comp
        if idx.sum() == 0: continue
        sub_y = y_test_1x2[idx]
        sub_pred = preds_1x2[idx]
        sub_prob = probs_1x2[idx]
        league_1x2[comp] = {
            "accuracy": round(float(accuracy_score(sub_y, sub_pred)), 4),
            "balanced_accuracy": round(float(balanced_accuracy_score(sub_y, sub_pred)), 4),
            "f1": round(float(f1_score(sub_y, sub_pred, average="macro")), 4),
            "log_loss": round(float(log_loss(sub_y, sub_prob, labels=[0,1,2])), 4),
        }

    return {
        "1x2_metrics": {
            "accuracy": round(float(acc), 4),
            "balanced_accuracy": round(float(bal_acc), 4),
            "macro_f1": round(float(f1), 4),
            "log_loss": round(float(ll), 4),
            "brier_score": round(float(brier), 4),
            "per_league": league_1x2,
        },
        "goal_metrics": {
            "home_mae": round(float(mae_h), 4),
            "home_rmse": round(float(rmse_h), 4),
            "away_mae": round(float(mae_a), 4),
            "away_rmse": round(float(rmse_a), 4),
        }
    }


def shadow_test_fixtures(v2_models_dict: dict) -> list[dict]:
    """Runs a shadow comparison test on real test fixtures across all 7 leagues."""
    from database.connection import SessionLocal
    from models import Match, Competition
    from ml.features import extract_ml_features

    db = SessionLocal()
    results = []

    target_comps = ["PL", "PD", "SA", "BL1", "FL1", "DED", "BSA"]

    wc_path = os.path.join(_MODELS_DIR, "world_cup_predictor.pkl")
    goal_path = os.path.join(_MODELS_DIR, "goal_predictor.pkl")
    with open(wc_path, "rb") as f: old_wc = pickle.load(f)
    with open(goal_path, "rb") as f: old_goal = pickle.load(f)

    for code in target_comps:
        comp = db.query(Competition).filter_by(code=code).first()
        if not comp: continue
        # Find one recent match
        m = db.query(Match).filter(
            Match.competition_id == comp.id,
            Match.home_team_id.isnot(None),
            Match.away_team_id.isnot(None)
        ).order_by(Match.utc_date.desc()).first()

        if not m: continue

        # Extract live features
        feats = extract_ml_features(db, m.home_team_id, m.away_team_id, m.utc_date, code)

        # 1. OLD MODEL PREDICTION
        old_vec = [feats.get(f, 0.0) for f in old_wc["features"]]
        old_probs = old_wc["model"].predict_proba(pd.DataFrame([old_vec], columns=old_wc["features"]))[0]
        old_g_vec = [feats.get(f, 0.0) for f in old_goal["features"]]
        old_home_xg = float(np.clip(old_goal["home_model"].predict(pd.DataFrame([old_g_vec], columns=old_goal["features"]))[0], 0, None))
        old_away_xg = float(np.clip(old_goal["away_model"].predict(pd.DataFrame([old_g_vec], columns=old_goal["features"]))[0], 0, None))

        # 2. V2 CLUB MODEL PREDICTION
        v2_vec = [feats.get(f, 0.0) for f in CLUB_FEATURES]
        v2_probs = v2_models_dict["variant_a_club"]["models"]["clf_1x2"].predict_proba(pd.DataFrame([v2_vec], columns=CLUB_FEATURES))[0]
        v2_home_xg = float(np.clip(v2_models_dict["variant_a_club"]["models"]["reg_home"].predict(pd.DataFrame([v2_vec], columns=CLUB_FEATURES))[0], 0, None))
        v2_away_xg = float(np.clip(v2_models_dict["variant_a_club"]["models"]["reg_away"].predict(pd.DataFrame([v2_vec], columns=CLUB_FEATURES))[0], 0, None))

        # 3. V2 COMBINED MODEL PREDICTION
        v2b_probs = v2_models_dict["variant_b_combined"]["models"]["clf_1x2"].predict_proba(pd.DataFrame([v2_vec], columns=CLUB_FEATURES))[0]
        v2b_home_xg = float(np.clip(v2_models_dict["variant_b_combined"]["models"]["reg_home"].predict(pd.DataFrame([v2_vec], columns=CLUB_FEATURES))[0], 0, None))
        v2b_away_xg = float(np.clip(v2_models_dict["variant_b_combined"]["models"]["reg_away"].predict(pd.DataFrame([v2_vec], columns=CLUB_FEATURES))[0], 0, None))

        # Map: 0=Away, 1=Draw, 2=Home
        def outcome_str(p):
            m = max(p)
            if m == p[2]: return "HOME_WIN"
            if m == p[0]: return "AWAY_WIN"
            return "DRAW"

        results.append({
            "competition": code,
            "home_team": m.home_team.name if m.home_team else "Home",
            "away_team": m.away_team.name if m.away_team else "Away",
            "match_date": str(m.utc_date)[:10],
            "old_model": {
                "home_p": round(float(old_probs[2]), 4),
                "draw_p": round(float(old_probs[1]), 4),
                "away_p": round(float(old_probs[0]), 4),
                "predicted": outcome_str(old_probs),
                "home_xg": round(old_home_xg, 2),
                "away_xg": round(old_away_xg, 2),
            },
            "v2_club": {
                "home_p": round(float(v2_probs[2]), 4),
                "draw_p": round(float(v2_probs[1]), 4),
                "away_p": round(float(v2_probs[0]), 4),
                "predicted": outcome_str(v2_probs),
                "home_xg": round(v2_home_xg, 2),
                "away_xg": round(v2_away_xg, 2),
            },
            "v2_combined": {
                "home_p": round(float(v2b_probs[2]), 4),
                "draw_p": round(float(v2b_probs[1]), 4),
                "away_p": round(float(v2b_probs[0]), 4),
                "predicted": outcome_str(v2b_probs),
                "home_xg": round(v2b_home_xg, 2),
                "away_xg": round(v2b_away_xg, 2),
            }
        })

    db.close()
    return results


def run_all_training_and_eval():
    df_club = load_club_dataset()
    df_combined = load_harmonized_combined_dataset()

    res_a = train_and_evaluate_variant("variant_a_club", df_club)
    res_b = train_and_evaluate_variant("variant_b_combined", df_combined)

    # Test old models on club test set
    _, test_df_club, _ = chronological_split(df_club, train_ratio=0.8)
    res_old = evaluate_old_models_on_club_test(test_df_club)

    # Shadow test on real fixtures
    shadow_res = shadow_test_fixtures({"variant_a_club": res_a, "variant_b_combined": res_b})

    # Package output report data
    eval_report_data = {
        "variant_a_club": res_a,
        "variant_b_combined": res_b,
        "old_model": res_old,
        "shadow_test": shadow_res,
    }

    # Clean non-serializable XGBoost objects
    del res_a["models"]
    del res_b["models"]

    out_file = os.path.join(_ROOT, "ml", "retraining_eval_results.json")
    with open(out_file, "w") as f:
        json.dump(eval_report_data, f, indent=2)

    logger.info(f"\nSaved evaluation results to {out_file}")
    return eval_report_data


if __name__ == "__main__":
    run_all_training_and_eval()
