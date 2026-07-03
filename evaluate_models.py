import pickle
import pandas as pd
import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    log_loss, brier_score_loss, roc_auc_score, roc_curve,
    confusion_matrix, mean_absolute_error, mean_squared_error, r2_score
)
from sklearn.calibration import calibration_curve

def evaluate_world_cup_model(model_path, dataset_path):
    """Evaluate world cup model with comprehensive metrics."""
    # Load data
    from ml.train_world_cup_model import FEATURES, TARGET
    df = pd.read_csv(dataset_path)
    
    available_features = [f for f in FEATURES if f in df.columns]
    df = df.dropna(subset=available_features)
    
    X = df[available_features].values
    y = df[TARGET].values
    
    # Load model
    with open(model_path, 'rb') as f:
        model_bundle = pickle.load(f)
    
    model = model_bundle['model']
    # Handle both old ('features') and new ('feature_names') formats
    feature_names = model_bundle.get('feature_names', model_bundle.get('features', []))
    
    # Align features
    feature_map = {f: i for i, f in enumerate(feature_names)}
    X_aligned = np.zeros((X.shape[0], len(feature_names)))
    for i, feat in enumerate(available_features):
        if feat in feature_map:
            X_aligned[:, feature_map[feat]] = X[:, i]
    
    # Predictions
    y_pred = model.predict(X_aligned)
    y_proba = model.predict_proba(X_aligned)
    
    # Metrics
    metrics = {}
    metrics['accuracy'] = accuracy_score(y, y_pred)
    metrics['precision_macro'] = precision_score(y, y_pred, average='macro')
    metrics['precision_weighted'] = precision_score(y, y_pred, average='weighted')
    metrics['recall_macro'] = recall_score(y, y_pred, average='macro')
    metrics['recall_weighted'] = recall_score(y, y_pred, average='weighted')
    metrics['f1_macro'] = f1_score(y, y_pred, average='macro')
    metrics['f1_weighted'] = f1_score(y, y_pred, average='weighted')
    metrics['log_loss'] = log_loss(y, y_proba)
    
    # Brier score for each class
    metrics['brier_score'] = np.mean([brier_score_loss((y == i).astype(int), y_proba[:, i]) for i in range(3)])
    
    # ROC AUC (one-vs-rest)
    try:
        metrics['roc_auc_ovr'] = roc_auc_score(y, y_proba, multi_class='ovr')
    except:
        metrics['roc_auc_ovr'] = None
    
    # Calibration
    prob_true, prob_pred = calibration_curve(y == 2, y_proba[:, 2], n_bins=10)
    metrics['calibration_error'] = np.mean(np.abs(prob_true - prob_pred))
    
    # Feature importance
    metrics['feature_importance'] = dict(zip(feature_names, model.feature_importances_))
    metrics['active_features'] = sum(imp > 0 for imp in model.feature_importances_)
    metrics['total_features'] = len(feature_names)
    
    # Confusion matrix
    cm = confusion_matrix(y, y_pred)
    metrics['confusion_matrix'] = cm
    
    return metrics, y, y_proba, feature_names

def evaluate_goal_model(model_path, dataset_path):
    """Evaluate goal model with comprehensive metrics."""
    # Load data
    from ml.train_goal_model import GOAL_FEATURES
    df = pd.read_csv(dataset_path)
    
    available_features = [f for f in GOAL_FEATURES if f in df.columns]
    df = df.dropna(subset=available_features + ['home_score', 'away_score'])
    
    X = df[available_features].values
    y_home = df['home_score'].values
    y_away = df['away_score'].values
    
    # Load model
    with open(model_path, 'rb') as f:
        model_bundle = pickle.load(f)
    
    home_model = model_bundle['home_model']
    away_model = model_bundle['away_model']
    # Handle both old ('features') and new ('feature_names') formats
    feature_names = model_bundle.get('feature_names', model_bundle.get('features', []))
    
    # Align features
    feature_map = {f: i for i, f in enumerate(feature_names)}
    X_aligned = np.zeros((X.shape[0], len(feature_names)))
    for i, feat in enumerate(available_features):
        if feat in feature_map:
            X_aligned[:, feature_map[feat]] = X[:, i]
    
    # Predictions
    y_home_pred = home_model.predict(X_aligned)
    y_away_pred = away_model.predict(X_aligned)
    
    # Metrics
    metrics = {}
    
    # Home goals
    metrics['home_mae'] = mean_absolute_error(y_home, y_home_pred)
    metrics['home_rmse'] = np.sqrt(mean_squared_error(y_home, y_home_pred))
    metrics['home_r2'] = r2_score(y_home, y_home_pred)
    
    # Away goals
    metrics['away_mae'] = mean_absolute_error(y_away, y_away_pred)
    metrics['away_rmse'] = np.sqrt(mean_squared_error(y_away, y_away_pred))
    metrics['away_r2'] = r2_score(y_away, y_away_pred)
    
    # Combined
    metrics['combined_mae'] = (metrics['home_mae'] + metrics['away_mae']) / 2
    metrics['combined_rmse'] = (metrics['home_rmse'] + metrics['away_rmse']) / 2
    metrics['combined_r2'] = (metrics['home_r2'] + metrics['away_r2']) / 2
    
    # Feature importance
    metrics['home_feature_importance'] = dict(zip(feature_names, home_model.feature_importances_))
    metrics['away_feature_importance'] = dict(zip(feature_names, away_model.feature_importances_))
    metrics['active_features'] = sum(imp > 0 for imp in home_model.feature_importances_)
    metrics['total_features'] = len(feature_names)
    
    return metrics, y_home, y_away, y_home_pred, y_away_pred, feature_names

def print_metrics_comparison(old_metrics, new_metrics, model_type):
    """Print comparison between old and new models."""
    print(f"\n{'='*80}")
    print(f"{model_type.upper()} MODEL COMPARISON")
    print(f"{'='*80}")
    
    print(f"\nOLD MODEL ↓")
    print(f"{'-'*80}")
    
    if model_type == 'world_cup':
        for key in ['accuracy', 'precision_macro', 'recall_macro', 'f1_macro', 'log_loss', 'brier_score', 'roc_auc_ovr']:
            if key in old_metrics:
                print(f"  {key:20s}: {old_metrics[key]:.4f}")
        print(f"  active_features     : {old_metrics['active_features']}/{old_metrics['total_features']}")
    else:
        for key in ['home_mae', 'home_rmse', 'home_r2', 'away_mae', 'away_rmse', 'away_r2', 'combined_mae', 'combined_rmse', 'combined_r2']:
            if key in old_metrics:
                print(f"  {key:20s}: {old_metrics[key]:.4f}")
        print(f"  active_features     : {old_metrics['active_features']}/{old_metrics['total_features']}")
    
    print(f"\nNEW MODEL ↓")
    print(f"{'-'*80}")
    
    if model_type == 'world_cup':
        for key in ['accuracy', 'precision_macro', 'recall_macro', 'f1_macro', 'log_loss', 'brier_score', 'roc_auc_ovr']:
            if key in new_metrics:
                print(f"  {key:20s}: {new_metrics[key]:.4f}")
        print(f"  active_features     : {new_metrics['active_features']}/{new_metrics['total_features']}")
    else:
        for key in ['home_mae', 'home_rmse', 'home_r2', 'away_mae', 'away_rmse', 'away_r2', 'combined_mae', 'combined_rmse', 'combined_r2']:
            if key in new_metrics:
                print(f"  {key:20s}: {new_metrics[key]:.4f}")
        print(f"  active_features     : {new_metrics['active_features']}/{new_metrics['total_features']}")
    
    print(f"\nIMPROVEMENT ↓")
    print(f"{'-'*80}")
    
    if model_type == 'world_cup':
        improvements = {}
        for key in ['accuracy', 'precision_macro', 'recall_macro', 'f1_macro']:
            if key in old_metrics and key in new_metrics:
                diff = new_metrics[key] - old_metrics[key]
                pct = (diff / old_metrics[key] * 100) if old_metrics[key] != 0 else 0
                improvements[key] = (diff, pct)
                print(f"  {key:20s}: {diff:+.4f} ({pct:+.2f}%)")
        
        for key in ['log_loss', 'brier_score']:
            if key in old_metrics and key in new_metrics:
                diff = old_metrics[key] - new_metrics[key]  # Lower is better
                pct = (diff / old_metrics[key] * 100) if old_metrics[key] != 0 else 0
                improvements[key] = (diff, pct)
                print(f"  {key:20s}: {diff:+.4f} ({pct:+.2f}%)")
        
        active_diff = new_metrics['active_features'] - old_metrics['active_features']
        print(f"  active_features     : {active_diff:+d}")
    else:
        improvements = {}
        for key in ['home_mae', 'home_rmse', 'away_mae', 'away_rmse', 'combined_mae', 'combined_rmse']:
            if key in old_metrics and key in new_metrics:
                diff = old_metrics[key] - new_metrics[key]  # Lower is better
                pct = (diff / old_metrics[key] * 100) if old_metrics[key] != 0 else 0
                improvements[key] = (diff, pct)
                print(f"  {key:20s}: {diff:+.4f} ({pct:+.2f}%)")
        
        for key in ['home_r2', 'away_r2', 'combined_r2']:
            if key in old_metrics and key in new_metrics:
                diff = new_metrics[key] - old_metrics[key]  # Higher is better
                pct = (diff / old_metrics[key] * 100) if old_metrics[key] != 0 else 0
                improvements[key] = (diff, pct)
                print(f"  {key:20s}: {diff:+.4f} ({pct:+.2f}%)")
        
        active_diff = new_metrics['active_features'] - old_metrics['active_features']
        print(f"  active_features     : {active_diff:+d}")
    
    return improvements

def compare_feature_importance(old_imp, new_imp, top_n=20):
    """Compare feature importance between old and new models."""
    print(f"\n{'='*80}")
    print(f"TOP {top_n} FEATURE IMPORTANCE COMPARISON")
    print(f"{'='*80}")
    
    # Get top features from new model
    sorted_new = sorted(new_imp.items(), key=lambda x: x[1], reverse=True)[:top_n]
    
    print(f"\n{'Feature':<40} {'Old':<10} {'New':<10} {'Change':<10}")
    print(f"{'-'*80}")
    
    for feat, new_val in sorted_new:
        old_val = old_imp.get(feat, 0.0)
        change = new_val - old_val
        print(f"{feat:<40} {old_val:<10.4f} {new_val:<10.4f} {change:+.4f}")

if __name__ == "__main__":
    print("="*80)
    print("MODEL EVALUATION AND COMPARISON - PHASE 4 OPTIMIZATION")
    print("="*80)
    
    # World Cup Model
    print("\n" + "="*80)
    print("EVALUATING WORLD CUP MODELS (PRE vs POST OPTIMIZATION)")
    print("="*80)
    
    old_wc_metrics, _, _, old_wc_features = evaluate_world_cup_model(
        'models/world_cup_predictor_pre_opt.pkl',
        'ml/dataset_world_cup.csv'
    )
    
    new_wc_metrics, _, _, new_wc_features = evaluate_world_cup_model(
        'models/world_cup_predictor.pkl',
        'ml/dataset_world_cup.csv'
    )
    
    wc_improvements = print_metrics_comparison(old_wc_metrics, new_wc_metrics, 'world_cup')
    compare_feature_importance(old_wc_metrics['feature_importance'], new_wc_metrics['feature_importance'])
    
    # Goal Model
    print("\n" + "="*80)
    print("EVALUATING GOAL MODELS (PRE vs POST OPTIMIZATION)")
    print("="*80)
    
    old_goal_metrics, _, _, _, _, old_goal_features = evaluate_goal_model(
        'models/goal_predictor_pre_opt.pkl',
        'ml/dataset_goals.csv'
    )
    
    new_goal_metrics, _, _, _, _, new_goal_features = evaluate_goal_model(
        'models/goal_predictor.pkl',
        'ml/dataset_goals.csv'
    )
    
    goal_improvements = print_metrics_comparison(old_goal_metrics, new_goal_metrics, 'goal')
    compare_feature_importance(old_goal_metrics['home_feature_importance'], new_goal_metrics['home_feature_importance'])
    
    print("\n" + "="*80)
    print("EVALUATION COMPLETE")
    print("="*80)
