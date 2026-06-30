#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, '/Users/anuragsaikia/prediction')

from database.connection import SessionLocal
from models import Team, Match, Competition

db = SessionLocal()

print("=== TEAMS IN DATABASE ===")
teams = db.query(Team).order_by(Team.name).all()
women_team_ids = [t.id for t in teams if any(s in t.name.lower() for s in ["women", "women's", "woman"])]

print("\n=== MATCHES WITH WOMEN'S TEAMS ===")
matches_with_women_teams = db.query(Match).filter(
    (Match.home_team_id.in_(women_team_ids)) | (Match.away_team_id.in_(women_team_ids))
).all()

competition_names = set()
for m in matches_with_women_teams:
    comp = db.query(Competition).filter_by(id=m.competition_id).first()
    if comp:
        competition_names.add(comp.name)
print(f"Competitions with women's matches: {sorted(competition_names)}")

print(f"\n=== CHECKING WC COMPETITION ===")
wc_comp = db.query(Competition).filter(Competition.code.like("%WC%")).all()
for comp in wc_comp:
    print(f"{comp.id:4} | {comp.name:60} | Code: {comp.code}")

db.close()
