
#!/usr/bin/env python3
import sys
import os
import pickle
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("EXAMINING TRAINED MODELS")
print("=" * 80)

print("\n--- 1. WORLD CUP PREDICTOR ---")
with open("models/world_cup_predictor.pkl", "rb") as f:
    wc_bundle = pickle.load(f)

print(f"\nBundle keys: {list(wc_bundle.keys())}")
if "model" in wc_bundle:
    model = wc_bundle["model"]
    print(f"Model class: {type(model)}")
    print(f"Model params: {model.get_params()}")
    if hasattr(model, "feature_importances_"):
        print("\n=== FEATURE IMPORTANCES (TOP 20) ===")
        features = wc_bundle.get("features", [])
        importances = model.feature_importances_
        for i in np.argsort(importances)[::-1][:20]:
            print(f"  {features[i]:<40} = {importances[i]:.6f}")
    if hasattr(model, "estimators_"):
        print("\n=== TREE INFO ===")
        print(f"Number of trees: {len(model.estimators_)}")
        if len(model.estimators_) > 0:
            print(f"First tree max depth: {model.estimators_[0].tree_.max_depth}")
            print(f"First tree num nodes: {model.estimators_[0].tree_.node_count}")

print("\n--- 2. GOAL PREDICTOR ---")
with open("models/goal_predictor.pkl", "rb") as f:
    goal_bundle = pickle.load(f)

print(f"\nBundle keys: {list(goal_bundle.keys())}")
for key in ["home_model", "away_model"]:
    if key in goal_bundle:
        model = goal_bundle[key]
        print(f"\n--- {key.upper()} ---")
        print(f"Model class: {type(model)}")
        print(f"Model params: {model.get_params()}")
        if hasattr(model, "feature_importances_"):
            print("\n=== FEATURE IMPORTANCES (TOP 20) ===")
            features = goal_bundle.get("features", [])
            importances = model.feature_importances_
            for i in np.argsort(importances)[::-1][:20]:
                print(f"  {features[i]:<40} = {importances[i]:.6f}")

print("\n--- Done! ---")
