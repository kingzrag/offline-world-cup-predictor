#!/usr/bin/env python3
"""
Verification script for betting market models.

Tests each trained model on the test set and generates detailed metrics:
- Accuracy, precision, recall, F1
- Log loss, Brier score
- Calibration plots
- Confusion matrices
- Feature importance
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any, Dict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    confusion_matrix,
    log_loss,
    precision_recall_fscore_support,
)
import seaborn as sns

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(PROJECT_ROOT))

from ml.train_betting_market_models import (
    META_COLUMNS,
    TARGET_ASIAN_HANDICAP,
    TARGET_ASIAN_TOTAL,
    TARGET_BTTS,
    TARGET_CLEAN_SHEET,
    TARGET_CORRECT_SCORE,
    feature_matrix,
)

ML_DIR = Path(__file__).resolve().parent
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


def load_model_bundle(market_name: str) -> Dict[str, Any]:
    """Load a trained model bundle."""
    model_path = MODELS_DIR / f"{market_name}_predictor.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")
    
    with open(model_path, "rb") as handle:
        return pickle.load(handle)


def load_test_data() -> pd.DataFrame:
    """Load the betting market dataset."""
    dataset_path = ML_DIR / "dataset_betting_markets.csv"
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")
    
    df = pd.read_csv(dataset_path)
    
    # Get feature columns
    feature_columns = [col for col in df.columns if col not in META_COLUMNS + [
        TARGET_ASIAN_HANDICAP, TARGET_ASIAN_TOTAL, TARGET_BTTS,
        TARGET_CLEAN_SHEET, TARGET_CORRECT_SCORE
    ]]
    
    # Chronological split
    df = df.sort_values(["utc_date", "match_id"]).reset_index(drop=True)
    n = len(df)
    val_end = int(n * 0.85)
    test_df = df.iloc[val_end:].copy()
    
    return test_df, feature_columns


def verify_model(market_name: str, target_column: str) -> Dict[str, Any]:
    """Verify a single betting market model."""
    print(f"\n{'=' * 60}")
    print(f"Verifying: {market_name}")
    print(f"{'=' * 60}")
    
    # Load model
    bundle = load_model_bundle(market_name)
    model = bundle["model"]
    feature_names = bundle["features"]
    
    # Load test data
    test_df, all_feature_columns = load_test_data()
    
    # Align features
    available_features = [f for f in feature_names if f in all_feature_columns]
    if len(available_features) != len(feature_names):
        print(f"Warning: {len(feature_names) - len(available_features)} features not found in test data")
    
    X_test = feature_matrix(test_df, available_features)
    y_test = test_df[target_column].to_numpy(dtype=int)
    
    # Predictions
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)
    
    # Metrics
    accuracy = float(accuracy_score(y_test, y_pred))
    
    try:
        ll = float(log_loss(y_test, y_proba))
    except:
        ll = 1.0
    
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, y_pred, average='weighted', zero_division=0
    )
    
    # Brier score (for binary classification)
    if y_proba.shape[1] == 2:
        pos_proba = y_proba[:, 1]
        brier = float(brier_score_loss(y_test, pos_proba))
    else:
        brier = None
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    
    # Calibration curve (for binary)
    calibration_data = None
    if y_proba.shape[1] == 2:
        prob_true, prob_pred = calibration_curve(y_test, pos_proba, n_bins=10)
        calibration_data = {
            "prob_true": prob_true.tolist(),
            "prob_pred": prob_pred.tolist(),
        }
    
    results = {
        "market_name": market_name,
        "test_samples": len(y_test),
        "accuracy": accuracy,
        "log_loss": ll,
        "precision_weighted": float(precision),
        "recall_weighted": float(recall),
        "f1_weighted": float(f1),
        "brier_score": brier,
        "confusion_matrix": cm.tolist(),
        "calibration": calibration_data,
        "feature_importance": bundle.get("feature_importance", []),
    }
    
    print(f"Test samples: {len(y_test)}")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Log loss: {ll:.4f}")
    print(f"F1 (weighted): {f1:.4f}")
    if brier is not None:
        print(f"Brier score: {brier:.4f}")
    
    return results


def plot_calibration(y_true: np.ndarray, y_proba: np.ndarray, market_name: str) -> Path:
    """Generate calibration plot."""
    if y_proba.ndim == 1:
        y_proba = np.column_stack([1 - y_proba, y_proba])
    
    pos_proba = y_proba[:, 1]
    prob_true, prob_pred = calibration_curve(y_true, pos_proba, n_bins=10)
    
    plt.figure(figsize=(8, 6))
    plt.plot([0, 1], [0, 1], "k:", label="Perfectly calibrated")
    plt.plot(prob_pred, prob_true, "s-", label=f"{market_name}")
    plt.xlabel("Mean predicted probability")
    plt.ylabel("Fraction of positives")
    plt.title(f"Calibration Curve - {market_name}")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plot_path = REPORTS_DIR / f"calibration_{market_name}.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return plot_path


def plot_confusion_matrix(cm: np.ndarray, market_name: str) -> Path:
    """Generate confusion matrix plot."""
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=True)
    plt.title(f"Confusion Matrix - {market_name}")
    plt.ylabel("True label")
    plt.xlabel("Predicted label")
    
    plot_path = REPORTS_DIR / f"confusion_matrix_{market_name}.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return plot_path


def generate_verification_report(results: list[Dict[str, Any]]) -> str:
    """Generate comprehensive verification report."""
    lines = [
        "# Betting Market Models Verification Report",
        "",
        f"Generated: {pd.Timestamp.now().isoformat()}",
        "",
        "## Model Performance Summary",
        "",
        "| Market | Test Samples | Accuracy | Log Loss | F1 (Weighted) | Brier Score |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    
    for result in results:
        brier_str = f"{result['brier_score']:.4f}" if result['brier_score'] else "N/A"
        lines.append(
            f"| {result['market_name']} | {result['test_samples']:,} | "
            f"{result['accuracy']:.4f} | {result['log_loss']:.4f} | "
            f"{result['f1_weighted']:.4f} | {brier_str} |"
        )
    
    lines.extend(["", "## Detailed Results", ""])
    
    for result in results:
        lines.extend([
            f"### {result['market_name'].replace('_', ' ').title()}",
            "",
            f"- **Test samples:** {result['test_samples']:,}",
            f"- **Accuracy:** {result['accuracy']:.4f}",
            f"- **Log loss:** {result['log_loss']:.4f}",
            f"- **Precision (weighted):** {result['precision_weighted']:.4f}",
            f"- **Recall (weighted):** {result['recall_weighted']:.4f}",
            f"- **F1 (weighted):** {result['f1_weighted']:.4f}",
        ])
        
        if result['brier_score'] is not None:
            lines.append(f"- **Brier score:** {result['brier_score']:.4f}")
        
        lines.extend([
            "",
            "#### Confusion Matrix",
            "",
        ])
        
        cm = np.array(result['confusion_matrix'])
        lines.append("```")
        lines.append(str(cm))
        lines.append("```")
        lines.extend([
            "",
            "#### Top Feature Importance",
            "",
            "| Rank | Feature | Importance |",
            "|---|---|---:|",
        ])
        
        for idx, (feature, importance) in enumerate(result['feature_importance'][:10], start=1):
            lines.append(f"| {idx} | `{feature}` | {importance:.6f} |")
        
        lines.append("")
    
    return "\n".join(lines)


def main():
    print("=" * 80)
    print("VERIFYING BETTING MARKET MODELS")
    print("=" * 80)
    
    markets = [
        ("asian_handicap", TARGET_ASIAN_HANDICAP),
        ("asian_total", TARGET_ASIAN_TOTAL),
        ("btts", TARGET_BTTS),
        ("clean_sheet", TARGET_CLEAN_SHEET),
        ("correct_score", TARGET_CORRECT_SCORE),
    ]
    
    results = []
    
    for market_name, target_column in markets:
        try:
            result = verify_model(market_name, target_column)
            results.append(result)
            
            # Generate plots for binary classification
            if result['brier_score'] is not None:
                # Load data for plotting
                test_df, all_feature_columns = load_test_data()
                bundle = load_model_bundle(market_name)
                model = bundle["model"]
                feature_names = bundle["features"]
                
                available_features = [f for f in feature_names if f in all_feature_columns]
                X_test = feature_matrix(test_df, available_features)
                y_test = test_df[target_column].to_numpy(dtype=int)
                y_proba = model.predict_proba(X_test)
                
                # Calibration plot
                plot_calibration(y_test, y_proba, market_name)
                
                # Confusion matrix plot
                cm = np.array(result['confusion_matrix'])
                plot_confusion_matrix(cm, market_name)
                
        except FileNotFoundError as e:
            print(f"❌ {market_name}: {e}")
        except Exception as e:
            print(f"❌ {market_name}: Error during verification: {e}")
    
    # Generate report
    if results:
        report = generate_verification_report(results)
        report_path = REPORTS_DIR / "betting_market_verification_report.md"
        report_path.write_text(report)
        
        print(f"\n{'=' * 80}")
        print(f"Verification report saved to: {report_path}")
        print(f"{'=' * 80}")
        
        # Summary
        print(f"\nVerified {len(results)} models successfully")
        for result in results:
            print(f"  ✅ {result['market_name']}: {result['accuracy']:.4f} accuracy")
    else:
        print("\n❌ No models verified successfully")


if __name__ == "__main__":
    main()
