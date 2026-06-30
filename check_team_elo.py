#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, '/Users/anuragsaikia/prediction')

from database.connection import SessionLocal
from models import TeamElo

db = SessionLocal()
print("="*100)
print("CHECKING TeamElo TABLE")
print("="*100)
elo_records = db.query(TeamElo).all()
print(f"Total TeamElo records: {len(elo_records)}")
for elo in elo_records:
    print(f"  - Team Name: '{elo.team_name}', Elo Rating: {elo.elo_rating}")
db.close()
