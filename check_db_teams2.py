#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, '/Users/anuragsaikia/prediction')

from database.connection import SessionLocal
from models import Team, Match

db = SessionLocal()

print("=== TEAMS IN DATABASE ===")
teams = db.query(Team).order_by(Team.name).all()

women_team_ids = []
men_team_ids = []
for t in teams:
    if any(s in t.name.lower() for s in ["women", "women's", "woman"]):
        women_team_ids.append(t.id)
    else:
        men_team_ids.append(t.id)

print("\n=== MATCHES WITH WOMEN'S TEAMS ===")
matches_with_women_teams = db.query(Match).filter(
    (Match.home_team_id.in_(women_team_ids)) | (Match.away_team_id.in_(women_team_ids))
).all()

print(f"Total matches with women's teams: {len(matches_with_women_teams)}")

print("\n=== NATIONAL TEAM PLAYERS IN WOMEN'S TEAMS ===")
from models import NationalTeamPlayer
women_players = db.query(NationalTeamPlayer).filter(
    NationalTeamPlayer.team_id.in_(women_team_ids)
).all()

print(f"National team players in women's teams: {len(women_players)}")

print("\n=== PREDICTIONS WITH WOMEN'S TEAMS ===")
from models import Prediction
preds_with_women_winners = db.query(Prediction).filter(
    Prediction.predicted_winner_id.in_(women_team_ids)
).all()
print(f"Predictions with women's teams as predicted winner: {len(preds_with_women_winners)}")

db.close()
