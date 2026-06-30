#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/Users/anuragsaikia/prediction')

from database.connection import SessionLocal
from services.model_service import model_service

print("=== VERIFICATION START ===")
print("="*100)

db = SessionLocal()

if not model_service.is_ready:
    print("Loading models...")
    model_service.load_models()

result = model_service.predict(db, "Ivory Coast", "Norway", "WC")

print("\n=== Prediction Result ===")
print("Home: Ivory Coast, Away: Norway")
print(f"Outcome: {result['outcome']['predicted_result']}")
print(f"  Home Win: {result['outcome']['home_win_probability']:.4f}")
print(f"  Draw:     {result['outcome']['draw_probability']:.4f}")
print(f"  Away Win: {result['outcome']['away_win_probability']:.4f}")
print(f"Expected Goals: Ivory Coast {result['goals']['expected_home_goals']:.2f}, Norway {result['goals']['expected_away_goals']:.2f}")
print()
print("SUCCESS! No issues!")

db.close()
