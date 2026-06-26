#!/usr/bin/env python3
"""
Retrain the existing international football ML models using the current feature pipeline.

Key guarantees:
- Uses only international FINISHED matches stored in PostgreSQL
- Uses the existing `extract_ml_features()` function directly
- Does not redesign model architecture; keeps XGBoost classifier/regressors
- Builds a reproducible historical dataset
- Compares new models against currently deployed bundles on the same validation/test splits
- Saves versioned v2 bundles only if they outperform deployed models
"""

from __future__ import annotations

import json
import math
import os
import pickle
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    log_loss,
    mean_absolute_error,
    mean_squared_error,
)
from sklearn.utils.class_weight import compute_sample_weight

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import SessionLocal
from ml.features import extract_ml_features
from models import Competition, Match
from utils.logger import logger

ML_DIR = Path(__file__).resolve().parent
MODELS_DIR = PROJECT_ROOT / "models"
DATASET_PATH = ML_DIR / "dataset_international_retrain.csv"
REPORT_PATH = PROJECT_ROOT / "MODEL_RETRAINING_REPORT.md"
WC_MODEL_PATH = MODELS_DIR / "world_cup_predictor.pkl"
GOAL_MODEL_PATH = MODELS_DIR / "goal_predictor.pkl"
WC_V2_MODEL_PATH = MODELS_DIR / "world_cup_predictor_v2.pkl"
GOAL_V2_MODEL_PATH = MODELS_DIR / "goal_predictor_v2.pkl"

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

TARGET_1X2 = "target"
TARGET_HOME_GOALS = "home_score"
TARGET_AWAY_GOALS = "away_score"
META_COLUMNS = [
    "match_id",
    "utc_date",
    "competition_code",
    "competition_name",
    "home_team",
    "away_team",
]
LABEL_MAP = {0: "Away Win", 1: "Draw", 2: "Home Win"}


@dataclass
class SplitData:
    train_df: pd.DataFrame
    val_df: pd.DataFrame
    test_df: pd.DataFrame


@dataclass
class ClassificationResult:
    model: xgb.XGBClassifier
    candidate_name: str
    params: Dict[str, Any]
    feature_names: List[str]
    val_metrics: Dict[str, float]
    test_metrics: Dict[str, float]
    feature_importance: List[Tuple[str, float]]


@dataclass
class GoalResult:
    home_model: xgb.XGBRegressor
    away_model: xgb.XGBRegressor
    candidate_name: str
    params: Dict[str, Any]
    feature_names: List[str]
    val_metrics: Dict[str, float]
    test_metrics: Dict[str, float]
    home_feature_importance: List[Tuple[str, float]]
    away_feature_importance: List[Tuple[str, float]]


def suppress_noisy_logs() -> None:
    try:
        import logging

        logger.setLevel(logging.WARNING)
        logging.getLogger("football_platform").setLevel(logging.WARNING)
    except Exception:
        pass


def classification_target_for_match(match: Match) -> Optional[int]:
    if match.winner == "HOME_TEAM":
        return 2
    if match.winner == "DRAW":
        return 1
    if match.winner == "AWAY_TEAM":
        return 0
    return None


def list_finished_international_matches(db) -> List[Match]:
    return (
        db.query(Match)
        .join(Competition, Competition.id == Match.competition_id)
        .filter(
            Match.status == "FINISHED",
            Match.home_score.isnot(None),
            Match.away_score.isnot(None),
            Competition.code.in_(INTERNATIONAL_CODES),
        )
        .order_by(Match.utc_date.asc(), Match.id.asc())
        .all()
    )


def build_retraining_dataset(
    force: bool = False,
) -> Tuple[pd.DataFrame, List[str], Dict[str, Any]]:
    if DATASET_PATH.exists() and not force:
        df = pd.read_csv(DATASET_PATH)
        feature_columns = [
            col
            for col in df.columns
            if col
            not in META_COLUMNS + [TARGET_1X2, TARGET_HOME_GOALS, TARGET_AWAY_GOALS]
        ]
        metadata = {
            "source": "cached_csv",
            "dataset_path": str(DATASET_PATH),
            "rows": len(df),
            "feature_count": len(feature_columns),
            "date_range": {
                "start": df["utc_date"].min() if not df.empty else None,
                "end": df["utc_date"].max() if not df.empty else None,
            },
        }
        return df, feature_columns, metadata

    suppress_noisy_logs()
    db = SessionLocal()
    rows: List[Dict[str, Any]] = []
    feature_columns: Optional[List[str]] = None
    skipped = 0
    try:
        matches = list_finished_international_matches(db)
        total = len(matches)
        if total == 0:
            raise RuntimeError("No finished international matches found in PostgreSQL.")

        print(
            f"Building retraining dataset from {total} finished international matches..."
        )
        for index, match in enumerate(matches, start=1):
            if index == 1 or index % 250 == 0:
                print(f"  processed {index - 1}/{total} matches", flush=True)
            competition = match.competition
            comp_code = competition.code if competition else "WC"
            try:
                features = extract_ml_features(
                    db,
                    match.home_team_id,
                    match.away_team_id,
                    match.utc_date,
                    competition_code=comp_code,
                    match_stage=match.stage,
                    match=match,
                )
                if feature_columns is None:
                    feature_columns = list(features.keys())
                target = classification_target_for_match(match)
                if target is None:
                    skipped += 1
                    continue
                row: Dict[str, Any] = {
                    "match_id": match.id,
                    "utc_date": match.utc_date.isoformat() if match.utc_date else None,
                    "competition_code": comp_code,
                    "competition_name": competition.name if competition else None,
                    "home_team": match.home_team.name if match.home_team else None,
                    "away_team": match.away_team.name if match.away_team else None,
                    TARGET_1X2: target,
                    TARGET_HOME_GOALS: int(match.home_score),
                    TARGET_AWAY_GOALS: int(match.away_score),
                }
                for feature_name in feature_columns:
                    value = features.get(feature_name, 0.0)
                    if value is None or (
                        isinstance(value, float) and math.isnan(value)
                    ):
                        value = 0.0
                    row[feature_name] = value
                rows.append(row)
            except Exception as exc:
                skipped += 1
                print(f"  warning: skipping match {match.id}: {exc}", flush=True)

        if not rows or not feature_columns:
            raise RuntimeError("Dataset build failed: no rows were extracted.")

        df = pd.DataFrame(rows)
        for feature_name in feature_columns:
            df[feature_name] = pd.to_numeric(df[feature_name], errors="coerce").fillna(
                0.0
            )

        df.to_csv(DATASET_PATH, index=False)
        metadata = {
            "source": "postgresql",
            "dataset_path": str(DATASET_PATH),
            "rows": len(df),
            "feature_count": len(feature_columns),
            "skipped_matches": skipped,
            "date_range": {
                "start": df["utc_date"].min() if not df.empty else None,
                "end": df["utc_date"].max() if not df.empty else None,
            },
            "international_codes": sorted(INTERNATIONAL_CODES),
        }
        return df, feature_columns, metadata
    finally:
        db.close()


def split_dataset(df: pd.DataFrame) -> SplitData:
    if df.empty:
        raise RuntimeError("Cannot split an empty dataset.")
    df = df.sort_values(["utc_date", "match_id"]).reset_index(drop=True)
    n = len(df)
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)
    if train_end <= 0 or val_end <= train_end or val_end >= n:
        raise RuntimeError(f"Dataset too small for train/val/test split: {n} rows")
    return SplitData(
        train_df=df.iloc[:train_end].copy(),
        val_df=df.iloc[train_end:val_end].copy(),
        test_df=df.iloc[val_end:].copy(),
    )


def feature_matrix(df: pd.DataFrame, feature_columns: List[str]) -> np.ndarray:
    return (
        df[feature_columns]
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0.0)
        .to_numpy(dtype=float)
    )


def evaluate_classifier(
    model: xgb.XGBClassifier, X: np.ndarray, y: np.ndarray
) -> Dict[str, float]:
    probs = model.predict_proba(X)
    preds = model.predict(X)
    return {
        "accuracy": float(accuracy_score(y, preds)),
        "log_loss": float(log_loss(y, probs, labels=[0, 1, 2])),
        "f1_macro": float(f1_score(y, preds, average="macro")),
        "f1_weighted": float(f1_score(y, preds, average="weighted")),
    }


def rank_importance(
    feature_names: List[str], importances: Iterable[float], top_n: int = 25
) -> List[Tuple[str, float]]:
    ranked = sorted(
        zip(feature_names, [float(x) for x in importances]),
        key=lambda item: item[1],
        reverse=True,
    )
    return ranked[:top_n]


def safe_engineered_features(feature_columns: List[str]) -> List[str]:
    preferred = [
        "home_goalkeeper_strength",
        "away_goalkeeper_strength",
        "goalkeeper_strength_diff",
        "home_passing_strength",
        "away_passing_strength",
        "passing_strength_diff",
        "home_recent_form",
        "away_recent_form",
        "recent_form_diff",
        "home_aerial_dominance",
        "away_aerial_dominance",
        "aerial_dominance_diff",
        "home_pressing_strength",
        "away_pressing_strength",
        "pressing_strength_diff",
        "home_defensive_stability",
        "away_defensive_stability",
        "defensive_stability_diff",
        "home_attacking_efficiency",
        "away_attacking_efficiency",
        "attacking_efficiency_diff",
        "home_finishing_quality",
        "away_finishing_quality",
        "finishing_quality_diff",
        "home_set_piece_strength",
        "away_set_piece_strength",
        "set_piece_strength_diff",
        "home_squad_availability",
        "away_squad_availability",
        "squad_availability_diff",
        "home_tactical_stability",
        "away_tactical_stability",
        "tactical_stability_diff",
    ]
    return [name for name in preferred if name in feature_columns]


def world_cup_feature_sets(
    all_feature_columns: List[str], old_wc_features: List[str]
) -> Dict[str, List[str]]:
    additions = safe_engineered_features(all_feature_columns)
    old_base = [name for name in old_wc_features if name in all_feature_columns]
    return {
        "wc_all_features_146": list(all_feature_columns),
        "wc_deployed_feature_set": old_base,
        "wc_deployed_plus_engineered": old_base
        + [name for name in additions if name not in old_base],
    }


def train_world_cup_model(
    split: SplitData, all_feature_columns: List[str], old_wc_features: List[str]
) -> ClassificationResult:
    y_train = split.train_df[TARGET_1X2].to_numpy(dtype=int)
    y_val = split.val_df[TARGET_1X2].to_numpy(dtype=int)
    y_test = split.test_df[TARGET_1X2].to_numpy(dtype=int)

    candidate_params = {
        "xgb_classifier_balanced_a": {
            "n_estimators": 500,
            "max_depth": 6,
            "learning_rate": 0.05,
            "subsample": 0.9,
            "colsample_bytree": 0.85,
            "min_child_weight": 2,
            "gamma": 0.05,
            "reg_alpha": 0.05,
            "reg_lambda": 1.2,
            "objective": "multi:softprob",
            "num_class": 3,
            "eval_metric": "mlogloss",
            "random_state": 42,
            "n_jobs": -1,
            "tree_method": "hist",
        },
        "xgb_classifier_balanced_b": {
            "n_estimators": 650,
            "max_depth": 5,
            "learning_rate": 0.04,
            "subsample": 0.85,
            "colsample_bytree": 0.85,
            "min_child_weight": 3,
            "gamma": 0.10,
            "reg_alpha": 0.10,
            "reg_lambda": 1.0,
            "objective": "multi:softprob",
            "num_class": 3,
            "eval_metric": "mlogloss",
            "random_state": 42,
            "n_jobs": -1,
            "tree_method": "hist",
        },
        "xgb_classifier_balanced_c": {
            "n_estimators": 400,
            "max_depth": 7,
            "learning_rate": 0.06,
            "subsample": 0.80,
            "colsample_bytree": 0.80,
            "min_child_weight": 2,
            "gamma": 0.15,
            "reg_alpha": 0.10,
            "reg_lambda": 1.5,
            "objective": "multi:softprob",
            "num_class": 3,
            "eval_metric": "mlogloss",
            "random_state": 42,
            "n_jobs": -1,
            "tree_method": "hist",
        },
    }

    best: Optional[ClassificationResult] = None
    for feature_set_name, feature_names in world_cup_feature_sets(
        all_feature_columns, old_wc_features
    ).items():
        X_train = feature_matrix(split.train_df, feature_names)
        X_val = feature_matrix(split.val_df, feature_names)
        X_test = feature_matrix(split.test_df, feature_names)
        sample_weight = compute_sample_weight(class_weight="balanced", y=y_train)
        for param_name, params in candidate_params.items():
            candidate_name = f"{feature_set_name}__{param_name}"
            print(f"Training WC classifier candidate: {candidate_name}")
            model = xgb.XGBClassifier(**params)
            model.fit(X_train, y_train, sample_weight=sample_weight, verbose=False)
            val_metrics = evaluate_classifier(model, X_val, y_val)
            test_metrics = evaluate_classifier(model, X_test, y_test)
            result = ClassificationResult(
                model=model,
                candidate_name=candidate_name,
                params=params,
                feature_names=feature_names,
                val_metrics=val_metrics,
                test_metrics=test_metrics,
                feature_importance=rank_importance(
                    feature_names, model.feature_importances_
                ),
            )
            if best is None:
                best = result
                continue
            if result.val_metrics["log_loss"] < best.val_metrics["log_loss"] or (
                math.isclose(
                    result.val_metrics["log_loss"],
                    best.val_metrics["log_loss"],
                    rel_tol=1e-9,
                    abs_tol=1e-9,
                )
                and result.val_metrics["accuracy"] > best.val_metrics["accuracy"]
            ):
                best = result

    assert best is not None
    return best


def evaluate_existing_wc_model(
    bundle: Dict[str, Any], split: SplitData, full_df_feature_columns: List[str]
) -> Dict[str, Dict[str, float]]:
    existing_features = bundle.get("features", [])
    model: xgb.XGBClassifier = bundle["model"]
    val_X = feature_matrix(split.val_df, existing_features)
    test_X = feature_matrix(split.test_df, existing_features)
    val_y = split.val_df[TARGET_1X2].to_numpy(dtype=int)
    test_y = split.test_df[TARGET_1X2].to_numpy(dtype=int)
    return {
        "validation": evaluate_classifier(model, val_X, val_y),
        "test": evaluate_classifier(model, test_X, test_y),
        "feature_count": len(existing_features),
    }


def goal_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    rmse = math.sqrt(mean_squared_error(y_true, y_pred))
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(rmse),
    }


def combine_goal_metrics(
    home: Dict[str, float], away: Dict[str, float]
) -> Dict[str, float]:
    return {
        "home_mae": home["mae"],
        "home_rmse": home["rmse"],
        "away_mae": away["mae"],
        "away_rmse": away["rmse"],
        "avg_mae": float((home["mae"] + away["mae"]) / 2.0),
        "avg_rmse": float((home["rmse"] + away["rmse"]) / 2.0),
    }


def evaluate_goal_models(
    home_model: xgb.XGBRegressor,
    away_model: xgb.XGBRegressor,
    X: np.ndarray,
    y_home: np.ndarray,
    y_away: np.ndarray,
    clip_zero: bool = True,
) -> Dict[str, float]:
    home_pred = home_model.predict(X)
    away_pred = away_model.predict(X)
    if clip_zero:
        home_pred = np.maximum(home_pred, 0.0)
        away_pred = np.maximum(away_pred, 0.0)
    return combine_goal_metrics(
        goal_metrics(y_home, home_pred), goal_metrics(y_away, away_pred)
    )


def goal_feature_sets(
    all_feature_columns: List[str], old_goal_features: List[str]
) -> Dict[str, List[str]]:
    additions = safe_engineered_features(all_feature_columns)
    old_base = [name for name in old_goal_features if name in all_feature_columns]
    return {
        "goal_all_features_146": list(all_feature_columns),
        "goal_deployed_feature_set": old_base,
        "goal_deployed_plus_engineered": old_base
        + [name for name in additions if name not in old_base],
    }


def train_goal_predictor(
    split: SplitData, all_feature_columns: List[str], old_goal_features: List[str]
) -> GoalResult:
    y_home_train = split.train_df[TARGET_HOME_GOALS].to_numpy(dtype=float)
    y_home_val = split.val_df[TARGET_HOME_GOALS].to_numpy(dtype=float)
    y_home_test = split.test_df[TARGET_HOME_GOALS].to_numpy(dtype=float)
    y_away_train = split.train_df[TARGET_AWAY_GOALS].to_numpy(dtype=float)
    y_away_val = split.val_df[TARGET_AWAY_GOALS].to_numpy(dtype=float)
    y_away_test = split.test_df[TARGET_AWAY_GOALS].to_numpy(dtype=float)

    candidate_params = {
        "xgb_goal_poisson_a": {
            "n_estimators": 500,
            "max_depth": 5,
            "learning_rate": 0.05,
            "subsample": 0.85,
            "colsample_bytree": 0.85,
            "min_child_weight": 2,
            "reg_alpha": 0.05,
            "reg_lambda": 1.0,
            "objective": "count:poisson",
            "eval_metric": "rmse",
            "random_state": 42,
            "n_jobs": -1,
            "tree_method": "hist",
        },
        "xgb_goal_poisson_b": {
            "n_estimators": 650,
            "max_depth": 4,
            "learning_rate": 0.04,
            "subsample": 0.90,
            "colsample_bytree": 0.80,
            "min_child_weight": 3,
            "reg_alpha": 0.10,
            "reg_lambda": 1.2,
            "objective": "count:poisson",
            "eval_metric": "rmse",
            "random_state": 42,
            "n_jobs": -1,
            "tree_method": "hist",
        },
        "xgb_goal_squared_error": {
            "n_estimators": 500,
            "max_depth": 5,
            "learning_rate": 0.05,
            "subsample": 0.85,
            "colsample_bytree": 0.85,
            "min_child_weight": 2,
            "reg_alpha": 0.05,
            "reg_lambda": 1.0,
            "objective": "reg:squarederror",
            "eval_metric": "rmse",
            "random_state": 42,
            "n_jobs": -1,
            "tree_method": "hist",
        },
    }

    best: Optional[GoalResult] = None
    for feature_set_name, feature_names in goal_feature_sets(
        all_feature_columns, old_goal_features
    ).items():
        X_train = feature_matrix(split.train_df, feature_names)
        X_val = feature_matrix(split.val_df, feature_names)
        X_test = feature_matrix(split.test_df, feature_names)
        for param_name, params in candidate_params.items():
            candidate_name = f"{feature_set_name}__{param_name}"
            print(f"Training goal candidate: {candidate_name}")
            home_model = xgb.XGBRegressor(**params)
            away_model = xgb.XGBRegressor(**params)
            home_model.fit(X_train, y_home_train, verbose=False)
            away_model.fit(X_train, y_away_train, verbose=False)
            val_metrics = evaluate_goal_models(
                home_model, away_model, X_val, y_home_val, y_away_val, clip_zero=True
            )
            test_metrics = evaluate_goal_models(
                home_model, away_model, X_test, y_home_test, y_away_test, clip_zero=True
            )
            result = GoalResult(
                home_model=home_model,
                away_model=away_model,
                candidate_name=candidate_name,
                params=params,
                feature_names=feature_names,
                val_metrics=val_metrics,
                test_metrics=test_metrics,
                home_feature_importance=rank_importance(
                    feature_names, home_model.feature_importances_
                ),
                away_feature_importance=rank_importance(
                    feature_names, away_model.feature_importances_
                ),
            )
            if best is None:
                best = result
                continue
            if result.val_metrics["avg_rmse"] < best.val_metrics["avg_rmse"] or (
                math.isclose(
                    result.val_metrics["avg_rmse"],
                    best.val_metrics["avg_rmse"],
                    rel_tol=1e-9,
                    abs_tol=1e-9,
                )
                and result.val_metrics["avg_mae"] < best.val_metrics["avg_mae"]
            ):
                best = result

    assert best is not None
    return best


def evaluate_existing_goal_model(
    bundle: Dict[str, Any], split: SplitData
) -> Dict[str, Any]:
    existing_features = bundle.get("features", [])
    home_model: xgb.XGBRegressor = bundle["home_model"]
    away_model: xgb.XGBRegressor = bundle["away_model"]
    val_X = feature_matrix(split.val_df, existing_features)
    test_X = feature_matrix(split.test_df, existing_features)
    val_y_home = split.val_df[TARGET_HOME_GOALS].to_numpy(dtype=float)
    val_y_away = split.val_df[TARGET_AWAY_GOALS].to_numpy(dtype=float)
    test_y_home = split.test_df[TARGET_HOME_GOALS].to_numpy(dtype=float)
    test_y_away = split.test_df[TARGET_AWAY_GOALS].to_numpy(dtype=float)
    return {
        "validation": evaluate_goal_models(
            home_model, away_model, val_X, val_y_home, val_y_away, clip_zero=True
        ),
        "test": evaluate_goal_models(
            home_model, away_model, test_X, test_y_home, test_y_away, clip_zero=True
        ),
        "feature_count": len(existing_features),
    }


def classification_outperforms(
    new_metrics: Dict[str, float], old_metrics: Dict[str, float]
) -> bool:
    return (
        new_metrics["log_loss"] < old_metrics["log_loss"]
        and new_metrics["accuracy"] >= old_metrics["accuracy"]
    ) or (
        new_metrics["log_loss"] <= old_metrics["log_loss"] * 0.995
        and new_metrics["f1_macro"] > old_metrics["f1_macro"]
    )


def goal_outperforms(
    new_metrics: Dict[str, float], old_metrics: Dict[str, float]
) -> bool:
    return (
        new_metrics["avg_rmse"] < old_metrics["avg_rmse"]
        and new_metrics["avg_mae"] <= old_metrics["avg_mae"]
    ) or (
        new_metrics["avg_rmse"] <= old_metrics["avg_rmse"] * 0.995
        and new_metrics["avg_mae"] < old_metrics["avg_mae"]
    )


def save_world_cup_v2(result: ClassificationResult) -> None:
    bundle = {
        "model": result.model,
        "features": result.feature_names,
        "label_map": LABEL_MAP,
        "label_encoder": None,
        "metrics": result.test_metrics,
        "version": "2.0",
        "trained_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z",
        "candidate_name": result.candidate_name,
        "params": result.params,
    }
    with open(WC_V2_MODEL_PATH, "wb") as handle:
        pickle.dump(bundle, handle)


def save_goal_v2(result: GoalResult) -> None:
    bundle = {
        "home_model": result.home_model,
        "away_model": result.away_model,
        "features": result.feature_names,
        "metrics": result.test_metrics,
        "version": "2.0",
        "trained_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z",
        "candidate_name": result.candidate_name,
        "params": result.params,
    }
    with open(GOAL_V2_MODEL_PATH, "wb") as handle:
        pickle.dump(bundle, handle)


def format_metric_table(title: str, metrics: Dict[str, Dict[str, float]]) -> List[str]:
    lines = [
        f"### {title}",
        "",
        "| Split | Accuracy | Log Loss | F1 Macro | F1 Weighted |",
        "|---|---:|---:|---:|---:|",
    ]
    for split_name, values in metrics.items():
        lines.append(
            f"| {split_name.title()} | {values['accuracy']:.4f} | {values['log_loss']:.4f} | {values['f1_macro']:.4f} | {values['f1_weighted']:.4f} |"
        )
    lines.append("")
    return lines


def format_goal_metric_table(
    title: str, metrics: Dict[str, Dict[str, float]]
) -> List[str]:
    lines = [
        f"### {title}",
        "",
        "| Split | Home MAE | Home RMSE | Away MAE | Away RMSE | Avg MAE | Avg RMSE |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for split_name, values in metrics.items():
        lines.append(
            f"| {split_name.title()} | {values['home_mae']:.4f} | {values['home_rmse']:.4f} | {values['away_mae']:.4f} | {values['away_rmse']:.4f} | {values['avg_mae']:.4f} | {values['avg_rmse']:.4f} |"
        )
    lines.append("")
    return lines


def build_report(
    dataset_metadata: Dict[str, Any],
    feature_columns: List[str],
    split: SplitData,
    wc_result: ClassificationResult,
    old_wc_metrics: Dict[str, Any],
    goal_result: GoalResult,
    old_goal_metrics: Dict[str, Any],
    wc_saved: bool,
    goal_saved: bool,
) -> str:
    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    lines: List[str] = []
    lines.append("# Model Retraining Report")
    lines.append("")
    lines.append(f"Generated: {now}")
    lines.append("")
    lines.append("## Dataset Summary")
    lines.append("")
    lines.append(f"- Matches used: **{dataset_metadata['rows']:,}**")
    lines.append(f"- Features used: **{len(feature_columns)}**")
    lines.append(f"- Dataset path: `{dataset_metadata['dataset_path']}`")
    lines.append(
        f"- Date range: **{dataset_metadata['date_range']['start']}** → **{dataset_metadata['date_range']['end']}**"
    )
    lines.append(
        f"- International competition codes: `{', '.join(dataset_metadata.get('international_codes', sorted(INTERNATIONAL_CODES)))}`"
    )
    lines.append(
        f"- Train / Validation / Test rows: **{len(split.train_df):,} / {len(split.val_df):,} / {len(split.test_df):,}**"
    )
    lines.append("")

    lines.append("## World Cup Predictor (1X2)")
    lines.append("")
    lines.append(f"- Selected candidate: `{wc_result.candidate_name}`")
    lines.append(
        f"- Selected feature subset: `{wc_result.candidate_name.split('__')[0]}`"
    )
    lines.append(
        f"- Current deployed feature count: **{old_wc_metrics['feature_count']}**"
    )
    lines.append(f"- Selected new feature count: **{len(wc_result.feature_names)}**")
    lines.append(f"- Saved versioned model: **{'Yes' if wc_saved else 'No'}**")
    lines.append(f"- Output path: `{WC_V2_MODEL_PATH}`")
    lines.append("")
    lines.extend(
        format_metric_table(
            "New model metrics",
            {"validation": wc_result.val_metrics, "test": wc_result.test_metrics},
        )
    )
    lines.extend(
        format_metric_table(
            "Current deployed model metrics",
            {
                "validation": old_wc_metrics["validation"],
                "test": old_wc_metrics["test"],
            },
        )
    )
    lines.append("#### Top Feature Importance")
    lines.append("")
    lines.append("| Rank | Feature | Importance |")
    lines.append("|---|---|---:|")
    for index, (feature_name, importance) in enumerate(
        wc_result.feature_importance, start=1
    ):
        lines.append(f"| {index} | `{feature_name}` | {importance:.6f} |")
    lines.append("")

    lines.append("## Goal Predictor")
    lines.append("")
    lines.append(f"- Selected candidate: `{goal_result.candidate_name}`")
    lines.append(
        f"- Selected feature subset: `{goal_result.candidate_name.split('__')[0]}`"
    )
    lines.append(
        f"- Current deployed feature count: **{old_goal_metrics['feature_count']}**"
    )
    lines.append(f"- Selected new feature count: **{len(goal_result.feature_names)}**")
    lines.append(f"- Saved versioned model: **{'Yes' if goal_saved else 'No'}**")
    lines.append(f"- Output path: `{GOAL_V2_MODEL_PATH}`")
    lines.append("")
    lines.extend(
        format_goal_metric_table(
            "New goal model metrics",
            {"validation": goal_result.val_metrics, "test": goal_result.test_metrics},
        )
    )
    lines.extend(
        format_goal_metric_table(
            "Current deployed goal model metrics",
            {
                "validation": old_goal_metrics["validation"],
                "test": old_goal_metrics["test"],
            },
        )
    )

    lines.append("#### Home Goal Model Feature Importance")
    lines.append("")
    lines.append("| Rank | Feature | Importance |")
    lines.append("|---|---|---:|")
    for index, (feature_name, importance) in enumerate(
        goal_result.home_feature_importance, start=1
    ):
        lines.append(f"| {index} | `{feature_name}` | {importance:.6f} |")
    lines.append("")
    lines.append("#### Away Goal Model Feature Importance")
    lines.append("")
    lines.append("| Rank | Feature | Importance |")
    lines.append("|---|---|---:|")
    for index, (feature_name, importance) in enumerate(
        goal_result.away_feature_importance, start=1
    ):
        lines.append(f"| {index} | `{feature_name}` | {importance:.6f} |")
    lines.append("")

    lines.append("## Comparison Summary")
    lines.append("")
    lines.append(
        f"- 1X2 deployed test accuracy/log loss/f1_macro: **{old_wc_metrics['test']['accuracy']:.4f} / {old_wc_metrics['test']['log_loss']:.4f} / {old_wc_metrics['test']['f1_macro']:.4f}**"
    )
    lines.append(
        f"- 1X2 new test accuracy/log loss/f1_macro: **{wc_result.test_metrics['accuracy']:.4f} / {wc_result.test_metrics['log_loss']:.4f} / {wc_result.test_metrics['f1_macro']:.4f}**"
    )
    lines.append(
        f"- Goal deployed avg test MAE/RMSE: **{old_goal_metrics['test']['avg_mae']:.4f} / {old_goal_metrics['test']['avg_rmse']:.4f}**"
    )
    lines.append(
        f"- Goal new avg test MAE/RMSE: **{goal_result.test_metrics['avg_mae']:.4f} / {goal_result.test_metrics['avg_rmse']:.4f}**"
    )
    lines.append("")
    lines.append("## Reproducibility")
    lines.append("")
    lines.append(
        "- Dataset is rebuilt from PostgreSQL using `extract_ml_features()` and historical FINISHED international matches only."
    )
    lines.append("- Splits are deterministic chronological splits (70/15/15).")
    lines.append("- XGBoost random state is fixed at `42`.")
    lines.append(
        f"- Retrain command: `python3 ml/retrain_international_models.py --force-rebuild`"
    )
    lines.append("")
    return "\n".join(lines)


def main(force_rebuild: bool = False) -> int:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    dataset_df, feature_columns, dataset_metadata = build_retraining_dataset(
        force=force_rebuild
    )
    split = split_dataset(dataset_df)

    with open(WC_MODEL_PATH, "rb") as handle:
        old_wc_bundle = pickle.load(handle)
    with open(GOAL_MODEL_PATH, "rb") as handle:
        old_goal_bundle = pickle.load(handle)

    wc_result = train_world_cup_model(
        split, feature_columns, old_wc_bundle.get("features", [])
    )
    old_wc_metrics = evaluate_existing_wc_model(old_wc_bundle, split, feature_columns)
    wc_saved = classification_outperforms(
        wc_result.test_metrics, old_wc_metrics["test"]
    )
    if wc_saved:
        save_world_cup_v2(wc_result)
        print(f"Saved improved 1X2 model -> {WC_V2_MODEL_PATH}")
    else:
        print(
            "1X2 model did not outperform deployed model on the held-out test set; not saving v2 bundle."
        )

    goal_result = train_goal_predictor(
        split, feature_columns, old_goal_bundle.get("features", [])
    )
    old_goal_metrics = evaluate_existing_goal_model(old_goal_bundle, split)
    goal_saved = goal_outperforms(goal_result.test_metrics, old_goal_metrics["test"])
    if goal_saved:
        save_goal_v2(goal_result)
        print(f"Saved improved goal model -> {GOAL_V2_MODEL_PATH}")
    else:
        print(
            "Goal model did not outperform deployed model on the held-out test set; not saving v2 bundle."
        )

    report = build_report(
        dataset_metadata,
        feature_columns,
        split,
        wc_result,
        old_wc_metrics,
        goal_result,
        old_goal_metrics,
        wc_saved,
        goal_saved,
    )
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Wrote training report -> {REPORT_PATH}")

    summary = {
        "dataset_rows": dataset_metadata["rows"],
        "feature_count": len(feature_columns),
        "world_cup_saved": wc_saved,
        "goal_saved": goal_saved,
        "world_cup_new_test": wc_result.test_metrics,
        "world_cup_old_test": old_wc_metrics["test"],
        "goal_new_test": goal_result.test_metrics,
        "goal_old_test": old_goal_metrics["test"],
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    force_rebuild = "--force-rebuild" in sys.argv
    raise SystemExit(main(force_rebuild=force_rebuild))
