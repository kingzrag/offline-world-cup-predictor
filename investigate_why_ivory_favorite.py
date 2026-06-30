#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/Users/anuragsaikia/prediction')

from database.connection import SessionLocal
from models import Team, TeamElo

db = SessionLocal()
print("="*100)
print("INVESTIGATION: IVORY COAST VS NORWAY")
print("="*100)

print("\n--- TEAMS ---")
ivory = db.query(Team).filter(Team.name.ilike("%ivory%"), Team.gender == "MEN").first()
norway = db.query(Team).filter(Team.name.ilike("%norway%"), Team.gender == "MEN").first()

print(f"Ivory Coast: id={ivory.id}, name='{ivory.name}', FIFA rank={ivory.fifa_ranking}, market value={ivory.market_value}, squad value={ivory.squad_market_value}")
print(f"Norway:      id={norway.id}, name='{norway.name}', FIFA rank={norway.fifa_ranking}, market value={norway.market_value}, squad value={norway.squad_market_value}")

print("\n--- TEAM ELO ---")
from ml.features import get_team_elo
ivory_elo = get_team_elo(db, ivory.name)
norway_elo = get_team_elo(db, norway.name)
print(f"Ivory Coast Elo: {ivory_elo}")
print(f"Norway Elo: {norway_elo}")

print("\n--- GETTING FEATURES ---")
from ml.features import extract_ml_features
from datetime import datetime, timezone
features = extract_ml_features(db, ivory.id, norway.id, datetime.now(timezone.utc), "WC")
print("All features:")
for k,v in sorted(features.items()):
    print(f"  {k:<30} = {v}")

db.close()
