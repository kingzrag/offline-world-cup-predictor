#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, '/Users/anuragsaikia/prediction')

from database.connection import SessionLocal
from models import TeamElo

db = SessionLocal()
print("="*100)
print("CHECKING TeamElo TABLE FOR 'Ivory' OR 'Norway'")
print("="*100)

from sqlalchemy import or_

elo_records = db.query(TeamElo).filter(
    or_(
        TeamElo.team_name.ilike("%ivory%"),
        TeamElo.team_name.ilike("%norway%")
    )
).all()

print(f"Found {len(elo_records)} relevant records:")
for elo in elo_records:
    print(f"  - '{elo.team_name}' = {elo.elo_rating}")
db.close()
