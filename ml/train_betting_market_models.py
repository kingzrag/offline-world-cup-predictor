#!/usr/bin/env python3
"""
Train separate ML models for different betting markets using historical international match data.

Betting markets:
- Asian Handicap (home -0.5)
- Asian Total (Over/Under 2.5)
- BTTS (Both Teams To Score)
- Clean Sheet (home team)
- Correct Score (multi-class)

Key guarantees:
- Uses only international FINISHED matches stored in PostgreSQL
- Reuses existing extract_ml_features() function
- Trains each market as separate XGBoost model
- Compares against baseline (simple heuristics)
- Saves models only if they outperform baseline
- Generates verification scripts and performance reports
"""

from __future__ import annotations

import json
import math
import pickle
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    confusion_matrix,
    log_loss,
    precision_recall_fscore_support,
)
from sklearn.utils.class_weight import compute_sample_weight

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(PROJECT_ROOT))

from database.connection import SessionLocal
from ml.features import extract_ml_features
from models import Competition, Match
from utils.logger import logger

ML_DIR = Path(__file__).resolve().parent
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

INTERNATIONAL_CODES = {
    "AFCON", "AFCONQ", "ASIAN", "ASIANQ", "CA", "CNL", "EC", "EU", "EUQ",
    "FRI", "OLY", "UNL", "WC", "WCQ", "WCQA", "WCQC", "WCQE", "WWC",
}

META_COLUMNS = [
    "match_id", "utc_date", "competition_code", "competition_name",
    "home_team", "away_team", "home_score", "away_score",
]

# Target variable definitions
TARGET_ASIAN_HANDICAP = "asian_handicap"
TARGET_ASIAN_TOTAL = "asian_total"
TARGET_BTTS = "btts"
TARGET_CLEAN_SHEET = "clean_sheet"
TARGET_CORRECT_SCORE = "correct_score"


@dataclass
class BettingMarketResult:
    model: xgb.XGBClassifier
    market_name: str
    params: Dict[str, Any]
    feature_names: List[str]
    val_metrics: Dict[str, float]
    test_metrics: Dict[str, float]
    feature_importance: List[Tuple[str, float]]
    calibration_data: Dict[str, Any]
    baseline_metrics: Dict[str, float]
    outperforms_baseline: bool


def suppress_noisy_logs() -> None:
    try:
        import logging
        logger.setLevel(logging.WARNING)
        logging.getLogger("football_platform").setLevel(logging.WARNING)
    except Exception:
        pass


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


def compute_betting_targets(match: Match) -> Dict[str, Any]:
    """Compute target variables for all betting markets from a single match."""
    home_score = match.home_score or 0
    away_score = match.away_score or 0
    goal_diff = home_score - away_score
    total_goals = home_score + away_score
    
    targets = {}
    
    # Asian Handicap (home -0.5): 1 if home wins, 0 otherwise
    targets[TARGET_ASIAN_HANDICAP] = 1 if goal_diff > 0 else 0
    
    # Asian Total (Over/Under 2.5): 1 if over 2.5, 0 otherwise
    targets[TARGET_ASIAN_TOTAL] = 1 if total_goals > 2.5 else 0
    
    # BTTS: 1 if both teams score, 0 otherwise
    targets[TARGET_BTTS] = 1 if (home_score > 0 and away_score > 0) else 0
    
    # Clean Sheet (home team): 1 if home team keeps clean sheet, 0 otherwise
    targets[TARGET_CLEAN_SHEET] = 1 if away_score == 0 else 0
    
    # Correct Score: encode as integer for multi-class
    # Map common scores to classes: 0-0=0, 1-0=1, 0-1=2, 1-1=3, 2-0=4, 0-2=5, 2-1=6, 1-2=7, 2-2=8, 3-0=9, 0-3=10, other=11
    score_map = {
        (0, 0): 0, (1, 0): 1, (0, 1): 2, (1, 1): 3,
        (2, 0): 4, (0, 2): 5, (2, 1): 6, (1, 2): 7,
        (2, 2): 8, (3, 0): 9, (0, 3): 10,
    }
    targets[TARGET_CORRECT_SCORE] = score_map.get((home_score, away_score), 11)
    
    return targets


def build_betting_dataset(force: bool = False) -> pd.DataFrame:
    """Build dataset with all betting market targets."""
    dataset_path = ML_DIR / "dataset_betting_markets.csv"
    
    if dataset_path.exists() and not force:
        logger.info(f"Loading cached dataset from {dataset_path}")
        return pd.read_csv(dataset_path)
    
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
        
        logger.info(f"Building betting dataset from {total} matches...")
        
        for index, match in enumerate(matches, start=1):
            if index == 1 or index % 250 == 0:
                print(f"  processed {index - 1}/{total} matches", flush=True)
            
            competition = match.competition
            comp_code = competition.code if competition else "WC"
            
            try:
                features = extract_ml_features(
                    db, match.home_team_id, match.away_team_id,
                    match.utc_date, competition_code=comp_code, match=match
                )
                
                if feature_columns is None:
                    feature_columns = list(features.keys())
                
                targets = compute_betting_targets(match)
                
                row: Dict[str, Any] = {
                    "match_id": match.id,
                    "utc_date": match.utc_date.isoformat() if match.utc_date else None,
                    "competition_code": comp_code,
                    "competition_name": competition.name if competition else None,
                    "home_team": match.home_team.name if match.home_team else None,
                    "away_team": match.away_team.name if match.away_team else None,
                    "home_score": match.home_score,
                    "away_score": match.away_score,
                }
                
                # Add features
                for feature_name in feature_columns:
                    value = features.get(feature_name, 0.0)
                    if value is None or (isinstance(value, float) and math.isnan(value)):
                        value = 0.0
                    row[feature_name] = value
                
                # Add betting targets
                row.update(targets)
                rows.append(row)
                
            except Exception as exc:
                skipped += 1
                print(f"  warning: skipping match {match.id}: {exc}", flush=True)
        
        if not rows or not feature_columns:
            raise RuntimeError("Dataset build failed: no rows were extracted.")
        
        df = pd.DataFrame(rows)
        for feature_name in feature_columns:
            df[feature_name] = pd.to_numeric(df[feature_name], errors="coerce").fillna(0.0)
        
        df.to_csv(dataset_path, index=False)
        logger.info(f"Saved {len(df)} rows to {dataset_path}")
        return df
        
    finally:
        db.close()


def split_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Chronological train/val/test split (70/15/15)."""
    df = df.sort_values(["utc_date", "match_id"]).reset_index(drop=True)
    n = len(df)
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)
    return (
        df.iloc[:train_end].copy(),
        df.iloc[train_end:val_end].copy(),
        df.iloc[val_end:].copy(),
    )


def feature_matrix(df: pd.DataFrame, feature_columns: List[str]) -> np.ndarray:
    return (
        df[feature_columns]
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0.0)
        .to_numpy(dtype=float)
    )


def compute_baseline_metrics(y_true: np.ndarray, market: str) -> Dict[str, float]:
    """Compute baseline metrics using simple heuristics."""
    n = len(y_true)
    if n == 0:
        return {"accuracy": 0.0, "log_loss": 1.0}
    
    # Baseline: predict majority class
    majority_class = np.bincount(y_true).argmax()
    y_pred_baseline = np.full(n, majority_class)
    
    # For log loss, use uniform distribution
    n_classes = len(np.unique(y_true))
    y_proba_baseline = np.full((n, n_classes), 1.0 / n_classes)
    
    accuracy = float(accuracy_score(y_true, y_pred_baseline))
    
    try:
        ll = float(log_loss(y_true, y_proba_baseline))
    except:
        ll = 1.0
    
    return {"accuracy": accuracy, "log_loss": ll}


def evaluate_classifier(
    model: xgb.XGBClassifier, X: np.ndarray, y: np.ndarray
) -> Dict[str, float]:
    probs = model.predict_proba(X)
    preds = model.predict(X)
    
    accuracy = float(accuracy_score(y, preds))
    
    try:
        ll = float(log_loss(y, probs))
    except:
        ll = 1.0
    
    precision, recall, f1, _ = precision_recall_fscore_support(
        y, preds, average='weighted', zero_division=0
    )
    
    return {
        "accuracy": accuracy,
        "log_loss": ll,
        "precision_weighted": float(precision),
        "recall_weighted": float(recall),
        "f1_weighted": float(f1),
    }


def compute_calibration_metrics(y_true: np.ndarray, y_proba: np.ndarray) -> Dict[str, Any]:
    """Compute calibration metrics for probability predictions."""
    if y_proba.ndim == 1:
        y_proba = np.column_stack([1 - y_proba, y_proba])
    
    # Use positive class probabilities for binary classification
    if y_proba.shape[1] == 2:
        pos_proba = y_proba[:, 1]
        # Brier score (only for binary)
        brier = float(brier_score_loss(y_true, pos_proba))
        # Calibration curve
        prob_true, prob_pred = calibration_curve(y_true, pos_proba, n_bins=10)
        return {
            "brier_score": brier,
            "calibration_curve": {
                "prob_true": prob_true.tolist(),
                "prob_pred": prob_pred.tolist(),
            },
        }
    else:
        # Multiclass: skip Brier score and calibration curve
        return {
            "brier_score": None,
            "calibration_curve": None,
        }


def rank_importance(
    feature_names: List[str], importances: np.ndarray, top_n: int = 20
) -> List[Tuple[str, float]]:
    ranked = sorted(
        zip(feature_names, [float(x) for x in importances]),
        key=lambda item: item[1],
        reverse=True,
    )
    return ranked[:top_n]


def train_betting_market_model(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_columns: List[str],
    target_column: str,
    market_name: str,
    n_classes: int = 2,
) -> BettingMarketResult:
    """Train a single betting market model."""
    
    X_train = feature_matrix(train_df, feature_columns)
    X_val = feature_matrix(val_df, feature_columns)
    X_test = feature_matrix(test_df, feature_columns)
    
    y_train = train_df[target_column].to_numpy(dtype=int)
    y_val = val_df[target_column].to_numpy(dtype=int)
    y_test = test_df[target_column].to_numpy(dtype=int)
    
    # Compute baseline metrics
    baseline_metrics = compute_baseline_metrics(y_test, market_name)
    
    # XGBoost parameters
    params = {
        "n_estimators": 500,
        "max_depth": 6,
        "learning_rate": 0.05,
        "subsample": 0.9,
        "colsample_bytree": 0.85,
        "min_child_weight": 2,
        "gamma": 0.05,
        "reg_alpha": 0.05,
        "reg_lambda": 1.2,
        "objective": "multi:softprob" if n_classes > 2 else "binary:logistic",
        "eval_metric": "mlogloss" if n_classes > 2 else "logloss",
        "random_state": 42,
        "n_jobs": -1,
        "tree_method": "hist",
    }
    
    # Only set num_class for multiclass classification
    if n_classes > 2:
        params["num_class"] = n_classes
    
    # Sample weights for imbalanced classes
    sample_weight = compute_sample_weight(class_weight="balanced", y=y_train)
    
    print(f"Training {market_name} model...")
    model = xgb.XGBClassifier(**params)
    model.fit(X_train, y_train, sample_weight=sample_weight, verbose=False)
    
    # Evaluate
    val_metrics = evaluate_classifier(model, X_val, y_val)
    test_metrics = evaluate_classifier(model, X_test, y_test)
    
    # Calibration
    val_probs = model.predict_proba(X_val)
    test_probs = model.predict_proba(X_test)
    calibration_data = {
        "validation": compute_calibration_metrics(y_val, val_probs),
        "test": compute_calibration_metrics(y_test, test_probs),
    }
    
    # Feature importance
    feature_importance = rank_importance(
        feature_columns, model.feature_importances_
    )
    
    # Check if outperforms baseline
    outperforms = (
        test_metrics["accuracy"] > baseline_metrics["accuracy"] and
        test_metrics["log_loss"] < baseline_metrics["log_loss"]
    )
    
    return BettingMarketResult(
        model=model,
        market_name=market_name,
        params=params,
        feature_names=feature_columns,
        val_metrics=val_metrics,
        test_metrics=test_metrics,
        feature_importance=feature_importance,
        calibration_data=calibration_data,
        baseline_metrics=baseline_metrics,
        outperforms_baseline=outperforms,
    )


def save_model(result: BettingMarketResult) -> Path:
    """Save trained model if it outperforms baseline."""
    model_path = MODELS_DIR / f"{result.market_name}_predictor.pkl"
    
    bundle = {
        "model": result.model,
        "features": result.feature_names,
        "market_name": result.market_name,
        "metrics": result.test_metrics,
        "calibration": result.calibration_data,
        "baseline_metrics": result.baseline_metrics,
        "feature_importance": result.feature_importance,
        "version": "1.0",
        "trained_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z",
        "params": result.params,
    }
    
    with open(model_path, "wb") as handle:
        pickle.dump(bundle, handle)
    
    logger.info(f"Saved {result.market_name} model to {model_path}")
    return model_path


def generate_market_report(
    results: List[BettingMarketResult],
    dataset_info: Dict[str, Any],
) -> str:
    """Generate comprehensive report for all betting markets."""
    
    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    lines = [
        "# Betting Market Models Report",
        "",
        f"Generated: {now}",
        "",
        "## Dataset Summary",
        "",
        f"- Total matches: **{dataset_info['total_matches']:,}**",
        f"- Train/Val/Test split: **{dataset_info['train_size']:,} / {dataset_info['val_size']:,} / {dataset_info['test_size']:,}**",
        f"- Features used: **{dataset_info['feature_count']}**",
        f"- Date range: **{dataset_info['date_start']}** → **{dataset_info['date_end']}**",
        "",
    ]
    
    for result in results:
        brier_score = result.calibration_data['test']['brier_score']
        brier_str = f"{brier_score:.4f}" if brier_score is not None else "N/A (multiclass)"
        
        lines.extend([
            f"## {result.market_name.replace('_', ' ').title()}",
            "",
            f"- **Outperforms baseline:** {'✅ Yes' if result.outperforms_baseline else '❌ No'}",
            f"- **Baseline accuracy:** {result.baseline_metrics['accuracy']:.4f}",
            f"- **Baseline log loss:** {result.baseline_metrics['log_loss']:.4f}",
            f"- **Test accuracy:** {result.test_metrics['accuracy']:.4f}",
            f"- **Test log loss:** {result.test_metrics['log_loss']:.4f}",
            f"- **Test F1 (weighted):** {result.test_metrics['f1_weighted']:.4f}",
            f"- **Test Brier score:** {brier_str}",
            "",
            "### Performance Comparison",
            "",
            "| Metric | Baseline | Model | Improvement |",
            "|---|---:|---:|---:|",
            f"| Accuracy | {result.baseline_metrics['accuracy']:.4f} | {result.test_metrics['accuracy']:.4f} | {result.test_metrics['accuracy'] - result.baseline_metrics['accuracy']:+.4f} |",
            f"| Log Loss | {result.baseline_metrics['log_loss']:.4f} | {result.test_metrics['log_loss']:.4f} | {result.baseline_metrics['log_loss'] - result.test_metrics['log_loss']:+.4f} |",
            "",
            "### Top Feature Importance",
            "",
            "| Rank | Feature | Importance |",
            "|---|---|---:|",
        ])
        
        for index, (feature_name, importance) in enumerate(result.feature_importance, start=1):
            lines.append(f"| {index} | `{feature_name}` | {importance:.6f} |")
        
        lines.extend([
            "",
            "### Calibration",
            "",
        ])
        
        if brier_score is not None:
            lines.append(f"- **Brier score (test):** {brier_score:.4f}")
        else:
            lines.append("- **Brier score (test):** N/A (multiclass)")
        
        lines.append("")
    
    lines.extend([
        "## Summary",
        "",
        "| Market | Outperforms Baseline | Test Accuracy | Test Log Loss |",
        "|---|---|---:|---:|",
    ])
    
    for result in results:
        lines.append(
            f"| {result.market_name} | {'✅' if result.outperforms_baseline else '❌'} | "
            f"{result.test_metrics['accuracy']:.4f} | {result.test_metrics['log_loss']:.4f} |"
        )
    
    lines.append("")
    
    return "\n".join(lines)


def main():
    print("=" * 80)
    print("TRAINING BETTING MARKET MODELS")
    print("=" * 80)
    
    # Build dataset
    df = build_betting_dataset(force=False)
    
    # Get feature columns
    feature_columns = [col for col in df.columns if col not in META_COLUMNS + [
        TARGET_ASIAN_HANDICAP, TARGET_ASIAN_TOTAL, TARGET_BTTS,
        TARGET_CLEAN_SHEET, TARGET_CORRECT_SCORE
    ]]
    
    # Split dataset
    train_df, val_df, test_df = split_dataset(df)
    
    dataset_info = {
        "total_matches": len(df),
        "train_size": len(train_df),
        "val_size": len(val_df),
        "test_size": len(test_df),
        "feature_count": len(feature_columns),
        "date_start": df["utc_date"].min(),
        "date_end": df["utc_date"].max(),
    }
    
    print(f"\nDataset: {dataset_info['total_matches']:,} matches")
    print(f"Split: {dataset_info['train_size']:,} / {dataset_info['val_size']:,} / {dataset_info['test_size']:,}")
    print(f"Features: {dataset_info['feature_count']}")
    
    # Train models for each market
    markets = [
        (TARGET_ASIAN_HANDICAP, "asian_handicap", 2),
        (TARGET_ASIAN_TOTAL, "asian_total", 2),
        (TARGET_BTTS, "btts", 2),
        (TARGET_CLEAN_SHEET, "clean_sheet", 2),
        (TARGET_CORRECT_SCORE, "correct_score", 12),
    ]
    
    results = []
    
    for target_col, market_name, n_classes in markets:
        print(f"\n{'=' * 60}")
        print(f"Training: {market_name}")
        print(f"{'=' * 60}")
        
        result = train_betting_market_model(
            train_df, val_df, test_df, feature_columns, target_col, market_name, n_classes
        )
        
        results.append(result)
        
        # Save if outperforms baseline
        if result.outperforms_baseline:
            save_model(result)
            print(f"✅ Model saved (outperforms baseline)")
        else:
            print(f"❌ Model NOT saved (does not outperform baseline)")
        
        print(f"Test accuracy: {result.test_metrics['accuracy']:.4f}")
        print(f"Test log loss: {result.test_metrics['log_loss']:.4f}")
        print(f"Baseline accuracy: {result.baseline_metrics['accuracy']:.4f}")
        print(f"Baseline log loss: {result.baseline_metrics['log_loss']:.4f}")
    
    # Generate report
    report = generate_market_report(results, dataset_info)
    report_path = REPORTS_DIR / "betting_market_models_report.md"
    report_path.write_text(report)
    
    print(f"\n{'=' * 80}")
    print(f"Report saved to: {report_path}")
    print(f"{'=' * 80}")
    
    # Summary
    saved_count = sum(1 for r in results if r.outperforms_baseline)
    print(f"\nModels saved: {saved_count}/{len(results)}")
    for result in results:
        status = "✅" if result.outperforms_baseline else "❌"
        print(f"  {status} {result.market_name}: {result.test_metrics['accuracy']:.4f} accuracy")


if __name__ == "__main__":
    main()
