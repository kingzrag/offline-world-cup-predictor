import os
import sys
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, log_loss

# Add root folder to sys.path so we can import from database/models
import pathlib, sys
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from utils.logger import logger

def train_pipeline():
    # 1. Load dataset
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(current_dir, "dataset.csv")
    
    if not os.path.exists(dataset_path):
        logger.error(f"Dataset not found at {dataset_path}. Please run build_dataset.py first.")
        return
        
    logger.info(f"Loading dataset from {dataset_path}...")
    df = pd.read_csv(dataset_path)
    
    # Separate features and target
    X = df.drop(columns=["target"])
    y = df["target"]
    
    logger.info(f"Dataset shape: {df.shape}")
    logger.info(f"Class distribution:\n{y.value_counts(normalize=True)}")

    # 2. Train/Test Split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # 3. Model Definition (XGBoost Classifier)
    # Using 'multi:softprob' which outputs class probabilities
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.05,
        objective="multi:softprob",
        num_class=3,
        eval_metric="mlogloss",
        random_state=42
    )

    # 4. Cross-Validation (5-fold)
    logger.info("Running 5-fold cross-validation...")
    cv_scores = cross_val_score(model, X, y, cv=5, scoring="accuracy")
    logger.info(f"Cross-Validation Accuracy Scores: {cv_scores}")
    logger.info(f"Mean CV Accuracy: {np.mean(cv_scores):.4f} (+/- {np.std(cv_scores):.4f})")

    # 5. Train Model
    logger.info("Training final XGBoost classifier...")
    model.fit(X_train, y_train)

    # 6. Evaluation Metrics on Holdout Test Set
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)
    
    acc = accuracy_score(y_test, y_pred)
    loss = log_loss(y_test, y_prob)
    
    logger.info(f"Holdout Test Accuracy: {acc:.4f}")
    logger.info(f"Holdout Test Log Loss: {loss:.4f}")

    # 7. Feature Importance Analysis
    importances = model.feature_importances_
    features_list = X.columns
    indices = np.argsort(importances)[::-1]
    
    logger.info("=== Feature Importance Analysis ===")
    for rank, idx in enumerate(indices):
        logger.info(f"{rank + 1}. Feature: {features_list[idx]:<12} | Importance: {importances[idx]:.4f}")

    # 8. Save Trained Model
    models_dir = os.path.join(current_dir, "models")
    os.makedirs(models_dir, exist_ok=True)
    model_save_path = os.path.join(models_dir, "xgboost_model.json")
    
    logger.info(f"Saving trained model to {model_save_path}...")
    model.save_model(model_save_path)
    logger.info("Model saved successfully. Pipeline complete.")

if __name__ == "__main__":
    train_pipeline()
