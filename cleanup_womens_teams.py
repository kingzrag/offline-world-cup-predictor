#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, '/Users/anuragsaikia/prediction')

from database.connection import SessionLocal
from models import Team, Match, Competition, TeamElo
from utils.logger import logger

def main():
    db = SessionLocal()
    try:
        # Find women's teams
        women_teams = db.query(Team).filter(
            (Team.gender == 'WOMEN') | 
            Team.name.ilike('%women%') | 
            Team.name.ilike('%woman%')
        ).all()
        
        women_team_ids = [t.id for t in women_teams]
        women_team_names = [t.name for t in women_teams]
        
        print(f"Found {len(women_teams)} women's teams to delete:")
        for name in sorted(women_team_names):
            print(f"  - {name}")
            
        # Find competition
        wwc_comp = db.query(Competition).filter(
            (Competition.code == 'WWC') | 
            Competition.name.ilike("%women%")
        ).first()
        
        if wwc_comp:
            print(f"\nFound women's competition to delete: {wwc_comp.name} (Code: {wwc_comp.code}, ID: {wwc_comp.id})")
            db.delete(wwc_comp)
            print("Deleted competition (cascades to standings/matches under it).")
            
        # Delete the teams explicitly
        for t in women_teams:
            db.delete(t)
        print(f"Deleted {len(women_teams)} women's teams (cascades to matches, players, standings, suspensions, injuries, etc.).")
        
        # Delete team ELO records
        elo_deleted = db.query(TeamElo).filter(
            TeamElo.team_name.in_(women_team_names) |
            TeamElo.team_name.ilike('%women%') |
            TeamElo.team_name.ilike('%woman%')
        ).delete(synchronize_session='fetch')
        print(f"Deleted {elo_deleted} records from team_elo table.")
        
        # Commit transaction
        db.commit()
        print("\n✅ Database cleanup transaction committed successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error during cleanup, rolled back transaction: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
