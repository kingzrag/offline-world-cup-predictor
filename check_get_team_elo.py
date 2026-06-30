#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, '/Users/anuragsaikia/prediction')

from database.connection import SessionLocal
from ml.features import get_team_elo
from models import Team

db = SessionLocal()

ivory_team = db.query(Team).filter(Team.name.ilike("%ivory%")).first()
norway_team = db.query(Team).filter(Team.name.ilike("%norway%") & ~Team.name.ilike("%women%")).first()

print("Ivory Coast team found:", ivory_team.name)
print("Norway team found:", norway_team.name)

print("calling get_team_elo for", ivory_team.name)
home_elo = get_team_elo(db, ivory_team.name)
print("home_elo:", home_elo)

print("calling get_team_elo for", norway_team.name)
away_elo = get_team_elo(db, norway_team.name)
print("away_elo:", away_elo)

db.close()
