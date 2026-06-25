#!/usr/bin/env python3
import pickle
import os

# Path to the model
model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "world_cup_predictor.pkl")
print(f"Loading model from {model_path}")
with open(model_path, "rb") as f:
    bundle = pickle.load(f)
print("-" * 80)
print("Model bundle keys:", list(bundle.keys()))
print("-" * 80)
print("Features used by model:")
for idx, feat in enumerate(bundle["features"]):
    print(f"{idx+1:2d}. {feat}")
print("-" * 80)
print("Model version:", bundle.get("version", "unknown"))
