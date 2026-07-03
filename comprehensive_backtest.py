"""
Comprehensive Historical Backtest
==================================
Compares old vs optimized models across all markets and metrics.
"""

import pickle
import pandas as pd
import numpy as np
from sklearn.metrics import (
    accuracy_score, log_loss, brier_score_loss,
    confusion_matrix
)
from scipy.stats import spearmanr
import warnings
warnings.filterwarnings('ignore')

def load_model(model_path):
    """Load model bundle and return model and metadata."""
    with open(model_path, 'rb') as f:
        bundle = pickle.load(f)
    
    # Handle different bundle structures
    if 'model' in bundle:
        # World cup model structure
        return bundle['model'], bundle.get('feature_names', bundle.get('features', []))
    elif 'home_model' in bundle:
        # Goal model structure
        return bundle, bundle.get('feature_names', bundle.get('features', []))
    else:
        raise ValueError(f"Unknown model structure in {model_path}")

def evaluate_1x2(model, X, y_true, feature_names):
    """Evaluate 1X2 (Home/Draw/Away) predictions."""
    # Get probabilities
    y_pred_proba = model.predict_proba(X[feature_names])
    
    # Get predictions
    y_pred = model.predict(X[feature_names])
    
    # Metrics
    accuracy = accuracy_score(y_true, y_pred)
    log_loss_val = log_loss(y_true, y_pred_proba, labels=['HOME_TEAM', 'DRAW', 'AWAY_TEAM'])
    
    # Brier score for each class
    brier_scores = {}
    for i, label in enumerate(['HOME_TEAM', 'DRAW', 'AWAY_TEAM']):
        y_binary = (y_true == label).astype(int)
        brier_scores[label] = brier_score_loss(y_binary, y_pred_proba[:, i])
    
    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred, labels=['HOME_TEAM', 'DRAW', 'AWAY_TEAM'])
    
    return {
        'accuracy': accuracy,
        'log_loss': log_loss_val,
        'brier_scores': brier_scores,
        'confusion_matrix': cm,
        'predictions': y_pred,
        'probabilities': y_pred_proba
    }

def evaluate_draw(model, X, y_true, feature_names):
    """Evaluate Draw predictions specifically."""
    y_pred_proba = model.predict_proba(X[feature_names])
    
    # Draw is index 1
    draw_proba = y_pred_proba[:, 1]
    draw_true = (y_true == 'DRAW').astype(int)
    
    # Predict draw if probability > 0.33
    draw_pred = (draw_proba > 0.33).astype(int)
    
    accuracy = accuracy_score(draw_true, draw_pred)
    log_loss_val = log_loss(draw_true, draw_proba)
    brier_score_val = brier_score_loss(draw_true, draw_proba)
    
    return {
        'accuracy': accuracy,
        'log_loss': log_loss_val,
        'brier_score': brier_score_val,
        'predictions': draw_pred,
        'probabilities': draw_proba
    }

def evaluate_double_chance(model, X, y_true, feature_names):
    """Evaluate Double Chance (Home/Draw, Draw/Away, Home/Away) predictions."""
    y_pred_proba = model.predict_proba(X[feature_names])
    
    # Double chance probabilities
    home_draw_proba = y_pred_proba[:, 0] + y_pred_proba[:, 1]  # Home or Draw
    draw_away_proba = y_pred_proba[:, 1] + y_pred_proba[:, 2]  # Draw or Away
    home_away_proba = y_pred_proba[:, 0] + y_pred_proba[:, 2]  # Home or Away
    
    # True outcomes
    home_draw_true = ((y_true == 'HOME_TEAM') | (y_true == 'DRAW')).astype(int)
    draw_away_true = ((y_true == 'DRAW') | (y_true == 'AWAY_TEAM')).astype(int)
    home_away_true = ((y_true == 'HOME_TEAM') | (y_true == 'AWAY_TEAM')).astype(int)
    
    # Predictions
    home_draw_pred = (home_draw_proba > 0.5).astype(int)
    draw_away_pred = (draw_away_proba > 0.5).astype(int)
    home_away_pred = (home_away_proba > 0.5).astype(int)
    
    return {
        'home_draw_accuracy': accuracy_score(home_draw_true, home_draw_pred),
        'draw_away_accuracy': accuracy_score(draw_away_true, draw_away_pred),
        'home_away_accuracy': accuracy_score(home_away_true, home_away_pred),
        'home_draw_brier': brier_score_loss(home_draw_true, home_draw_proba),
        'draw_away_brier': brier_score_loss(draw_away_true, draw_away_proba),
        'home_away_brier': brier_score_loss(home_away_true, home_away_proba)
    }

def evaluate_goals(goal_model, X, y_true_home, y_true_away, feature_names):
    """Evaluate Home/Away Goals predictions."""
    # goal_model is a bundle with home_model and away_model
    home_model = goal_model['home_model']
    away_model = goal_model['away_model']
    
    y_pred_home = home_model.predict(X[feature_names])
    y_pred_away = away_model.predict(X[feature_names])
    
    # Metrics
    home_mae = np.mean(np.abs(y_pred_home - y_true_home))
    home_rmse = np.sqrt(np.mean((y_pred_home - y_true_home)**2))
    
    away_mae = np.mean(np.abs(y_pred_away - y_true_away))
    away_rmse = np.sqrt(np.mean((y_pred_away - y_true_away)**2))
    
    # Correlation
    home_corr, _ = spearmanr(y_pred_home, y_true_home)
    away_corr, _ = spearmanr(y_pred_away, y_true_away)
    
    return {
        'home_mae': home_mae,
        'home_rmse': home_rmse,
        'home_correlation': home_corr,
        'away_mae': away_mae,
        'away_rmse': away_rmse,
        'away_correlation': away_corr,
        'predictions_home': y_pred_home,
        'predictions_away': y_pred_away
    }

def evaluate_btts(goal_model, X, y_true_home, y_true_away, feature_names):
    """Evaluate Both Teams To Score (BTTS) predictions."""
    home_pred = goal_model['home_model'].predict(X[feature_names])
    away_pred = goal_model['away_model'].predict(X[feature_names])
    
    # BTTS probability using Poisson approximation
    btts_proba = (1 - np.exp(-home_pred)) * (1 - np.exp(-away_pred))
    btts_true = ((y_true_home > 0) & (y_true_away > 0)).astype(int)
    
    # Predict BTTS if probability > 0.5
    btts_pred = (btts_proba > 0.5).astype(int)
    
    accuracy = accuracy_score(btts_true, btts_pred)
    brier_score_val = brier_score_loss(btts_true, btts_proba)
    
    return {
        'accuracy': accuracy,
        'brier_score': brier_score_val,
        'predictions': btts_pred,
        'probabilities': btts_proba
    }

def evaluate_over_under(goal_model, X, y_true_home, y_true_away, feature_names, threshold=2.5):
    """Evaluate Over/Under 2.5 Goals predictions."""
    home_pred = goal_model['home_model'].predict(X[feature_names])
    away_pred = goal_model['away_model'].predict(X[feature_names])
    
    total_pred = home_pred + away_pred
    total_true = y_true_home + y_true_away
    
    over_true = (total_true > threshold).astype(int)
    over_proba = (total_pred > threshold).astype(float)
    
    # Predict over if total > threshold
    over_pred = (total_pred > threshold).astype(int)
    
    accuracy = accuracy_score(over_true, over_pred)
    brier_score_val = brier_score_loss(over_true, over_proba)
    
    return {
        'accuracy': accuracy,
        'brier_score': brier_score_val,
        'predictions': over_pred,
        'probabilities': over_proba
    }

def evaluate_asian_handicap(model, X, y_true, feature_names):
    """Evaluate Asian Handicap predictions (simplified)."""
    y_pred_proba = model.predict_proba(X[feature_names])
    
    # Simplified: use probability difference as handicap prediction
    home_advantage = y_pred_proba[:, 0] - y_pred_proba[:, 2]
    
    # True outcome (home win = +1, draw = 0, away win = -1)
    outcome_numeric = np.where(y_true == 'HOME_TEAM', 1, np.where(y_true == 'DRAW', 0, -1))
    
    # Predict home advantage if > 0
    handicap_pred = (home_advantage > 0).astype(int)
    handicap_true = (outcome_numeric > 0).astype(int)
    
    accuracy = accuracy_score(handicap_true, handicap_pred)
    
    return {
        'accuracy': accuracy,
        'predictions': handicap_pred,
        'home_advantage': home_advantage
    }

def evaluate_correct_score(goal_model, X, y_true_home, y_true_away, feature_names):
    """Evaluate Correct Score predictions (simplified)."""
    home_pred = goal_model['home_model'].predict(X[feature_names])
    away_pred = goal_model['away_model'].predict(X[feature_names])
    
    # Round to nearest integer
    home_pred_int = np.round(home_pred).astype(int)
    away_pred_int = np.round(away_pred).astype(int)
    
    # Exact match
    correct_score = ((home_pred_int == y_true_home) & (away_pred_int == y_true_away)).astype(int)
    
    accuracy = np.mean(correct_score)
    
    # Within 1 goal
    within_1 = ((np.abs(home_pred_int - y_true_home) <= 1) & 
                (np.abs(away_pred_int - y_true_away) <= 1)).astype(int)
    accuracy_within_1 = np.mean(within_1)
    
    return {
        'exact_accuracy': accuracy,
        'within_1_accuracy': accuracy_within_1,
        'predictions_home': home_pred_int,
        'predictions_away': away_pred_int
    }

def evaluate_calibration(y_true, y_pred_proba, n_bins=10):
    """Evaluate calibration using reliability diagram (manual implementation)."""
    # Create bins
    bins = np.linspace(0, 1, n_bins + 1)
    bin_centers = (bins[:-1] + bins[1:]) / 2
    
    prob_true = []
    prob_pred = []
    
    for i in range(n_bins):
        # Get samples in this bin
        mask = (y_pred_proba >= bins[i]) & (y_pred_proba < bins[i+1])
        if np.sum(mask) > 0:
            prob_true.append(np.mean(y_true[mask]))
            prob_pred.append(np.mean(y_pred_proba[mask]))
        else:
            prob_true.append(0.0)
            prob_pred.append(bin_centers[i])
    
    # Expected Calibration Error (ECE)
    ece = 0.0
    for i in range(len(prob_pred)):
        ece += np.abs(prob_true[i] - prob_pred[i]) * prob_pred[i]
    ece = ece / len(prob_pred)
    
    return {
        'prob_true': prob_true,
        'prob_pred': prob_pred,
        'ece': ece
    }

def evaluate_confidence(y_pred_proba):
    """Evaluate confidence metrics."""
    max_proba = np.max(y_pred_proba, axis=1)
    confidence_mean = np.mean(max_proba)
    confidence_std = np.std(max_proba)
    
    # High confidence predictions (> 0.7)
    high_conf_mask = max_proba > 0.7
    high_conf_ratio = np.mean(high_conf_mask)
    
    return {
        'mean_confidence': confidence_mean,
        'std_confidence': confidence_std,
        'high_confidence_ratio': high_conf_ratio
    }

def calculate_roi(y_true, y_pred, odds, stake=1.0):
    """Calculate ROI if odds are available."""
    # Simplified ROI calculation
    # In practice, would need actual odds data
    if odds is None:
        return {'roi': 0.0, 'total_bets': 0, 'winning_bets': 0}
    
    total_profit = 0.0
    total_bets = len(y_pred)
    winning_bets = 0
    
    for i in range(len(y_pred)):
        if y_pred[i] == y_true[i]:
            total_profit += odds[i] * stake - stake
            winning_bets += 1
        else:
            total_profit -= stake
    
    roi = (total_profit / (total_bets * stake)) * 100 if total_bets > 0 else 0.0
    
    return {
        'roi': roi,
        'total_bets': total_bets,
        'winning_bets': winning_bets,
        'win_rate': winning_bets / total_bets if total_bets > 0 else 0.0
    }

def run_comprehensive_backtest():
    """Run comprehensive backtest comparing old vs optimized models."""
    print("="*80)
    print("COMPREHENSIVE HISTORICAL BACKTEST")
    print("="*80)
    print("\nUsing existing evaluation infrastructure from evaluate_models.py")
    print("This ensures proper data handling and metric calculation.")
    
    # Import the existing evaluation functions
    import sys
    sys.path.append('.')
    from evaluate_models import evaluate_world_cup_model, evaluate_goal_model
    
    # Load datasets
    print("\nLoading datasets...")
    df_wc = pd.read_csv('ml/dataset_world_cup.csv')
    df_goals = pd.read_csv('ml/dataset_goals.csv')
    
    # Load models
    print("Loading models...")
    old_wc_model, old_wc_features = load_model('models/world_cup_predictor_pre_opt.pkl')
    new_wc_model, new_wc_features = load_model('models/world_cup_predictor.pkl')
    
    # Goal models are bundles with home_model and away_model
    with open('models/goal_predictor_pre_opt.pkl', 'rb') as f:
        old_goal_bundle = pickle.load(f)
    old_goal_model = old_goal_bundle
    old_goal_features = old_goal_bundle.get('feature_names', old_goal_bundle.get('features', []))
    
    with open('models/goal_predictor.pkl', 'rb') as f:
        new_goal_bundle = pickle.load(f)
    new_goal_model = new_goal_bundle
    new_goal_features = new_goal_bundle.get('feature_names', new_goal_bundle.get('features', []))
    
    print(f"\nWorld Cup dataset: {len(df_wc)} rows")
    print(f"Goals dataset: {len(df_goals)} rows")
    
    # Use existing evaluation infrastructure
    print("\n" + "="*80)
    print("WORLD CUP MODEL EVALUATION")
    print("="*80)
    
    print("\n--- OLD MODEL ---")
    old_wc_metrics, _, _, _ = evaluate_world_cup_model(
        'models/world_cup_predictor_pre_opt.pkl',
        'ml/dataset_world_cup.csv'
    )
    
    print("\n--- NEW MODEL ---")
    new_wc_metrics, _, _, _ = evaluate_world_cup_model(
        'models/world_cup_predictor.pkl',
        'ml/dataset_world_cup.csv'
    )
    
    print("\n--- IMPROVEMENT ---")
    acc_improvement = (new_wc_metrics['accuracy'] - old_wc_metrics['accuracy']) * 100
    log_loss_improvement = (old_wc_metrics['log_loss'] - new_wc_metrics['log_loss']) / old_wc_metrics['log_loss'] * 100
    brier_improvement = (old_wc_metrics['brier_score'] - new_wc_metrics['brier_score']) / old_wc_metrics['brier_score'] * 100
    print(f"Accuracy: {acc_improvement:+.2f}%")
    print(f"Log Loss: {log_loss_improvement:+.2f}%")
    print(f"Brier Score: {brier_improvement:+.2f}%")
    
    # Evaluate Goal Model
    print("\n" + "="*80)
    print("GOAL MODEL EVALUATION")
    print("="*80)
    
    print("\n--- OLD MODEL ---")
    old_goal_metrics, _, _, _, _, _ = evaluate_goal_model(
        'models/goal_predictor_pre_opt.pkl',
        'ml/dataset_goals.csv'
    )
    
    print("\n--- NEW MODEL ---")
    new_goal_metrics, _, _, _, _, _ = evaluate_goal_model(
        'models/goal_predictor.pkl',
        'ml/dataset_goals.csv'
    )
    
    print("\n--- IMPROVEMENT ---")
    mae_improvement = (old_goal_metrics['home_mae'] - new_goal_metrics['home_mae']) / old_goal_metrics['home_mae'] * 100
    rmse_improvement = (old_goal_metrics['home_rmse'] - new_goal_metrics['home_rmse']) / old_goal_metrics['home_rmse'] * 100
    r2_improvement = (new_goal_metrics['home_r2'] - old_goal_metrics['home_r2']) / old_goal_metrics['home_r2'] * 100
    print(f"Home MAE: {mae_improvement:+.2f}%")
    print(f"Home RMSE: {rmse_improvement:+.2f}%")
    print(f"Home R²: {r2_improvement:+.2f}%")
    
    # Collect all results for report generation
    results = {
        'old_wc': old_wc_metrics,
        'new_wc': new_wc_metrics,
        'old_goal': old_goal_metrics,
        'new_goal': new_goal_metrics
    }
    
    print("\n" + "="*80)
    print("BACKTEST COMPLETE")
    print("="*80)
    
    return results

if __name__ == "__main__":
    results = run_comprehensive_backtest()
