#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, '/Users/anuragsaikia/prediction')

from database.connection import SessionLocal
from models import Team, TeamElo, NationalTeamPlayer, Match

db = SessionLocal()

print("=== TEAMS IN DATABASE ===")
teams = db.query(Team).order_by(Team.name).all()
print(f"Total: {len(teams)}")

women_teams = []
men_teams = []
for t in teams:
    if any(s in t.name.lower() for s in ["women", "women's", "woman"]):
        women_teams.append(t)
    else:
        men_teams.append(t)

print(f"Men's teams: {len(men_teams)}")
print(f"Women's teams: {len(women_teams)}")
if len(women_teams) > 0:
    print("\n-- Women's Teams --")
    for t in women_teams:
        print(f"  {t.id:4} | {t.name:40} | FIFA Rank: {t.fifa_ranking}")

print(f"\n--- TEAM ELO RECORDS -- {len(db.query(TeamElo).all())} --")

print("\n--- MATCHES --")
matches = db.query(Match).all()
print(f"Total matches: {len(matches)}")

print("\n--- NATIONAL TEAM PLAYERS --")
players = db.query(NationalTeamPlayer).all()
print(f"Total national team players: {len(players)}")

db.close()
