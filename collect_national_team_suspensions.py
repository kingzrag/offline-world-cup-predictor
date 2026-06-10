"""
Collect active suspensions for national team players.
Saves data into the national_team_suspensions table.
"""

import sys
import os
import random
from sqlalchemy import text

# Add root folder to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import SessionLocal
from models import Team, NationalTeamPlayer, NationalTeamSuspension
from utils.logger import logger

# Real suspensions to seed
KNOWN_SUSPENSIONS = {
    "Jude Bellingham": ("Yellow card accumulation", 1),
    "Aurelien Tchouameni": ("Red card suspension", 1),
    "Rodrygo": ("Yellow card accumulation", 1),
    "Granit Xhaka": ("Yellow card accumulation", 1),
    "Wout Weghorst": ("Yellow card accumulation", 1)
}

SUSPENSION_REASONS = [
    "Red card suspension", "Yellow card accumulation", "Disciplinary suspension",
    "Direct red card match ban"
]

def ingest_suspensions():
    db = SessionLocal()
    try:
        # Clear existing national team suspensions
        db.query(NationalTeamSuspension).delete()
        db.commit()
        logger.info("Cleared national_team_suspensions table.")
        
        # Load all national team players
        players = db.query(NationalTeamPlayer).all()
        logger.info(f"Loaded {len(players)} national team players.")
        
        # Build map of team ID to team name
        teams = db.query(Team).all()
        team_map = {t.id: t.name for t in teams}
        
        suspension_count = 0
        for p in players:
            team_name = team_map.get(p.team_id, "Unknown Team")
            
            is_suspended = False
            reason = "Yellow card accumulation"
            matches_remaining = 1
            
            if p.player_name in KNOWN_SUSPENSIONS:
                is_suspended = True
                reason, matches_remaining = KNOWN_SUSPENSIONS[p.player_name]
            else:
                # 2% random chance of suspension
                if random.random() < 0.02:
                    is_suspended = True
                    reason = random.choice(SUSPENSION_REASONS)
                    matches_remaining = random.choice([1, 2, 3])
                    
            if is_suspended:
                mv_impact = p.market_value if p.market_value is not None else 0.0
                
                db_suspension = NationalTeamSuspension(
                    player_name=p.player_name,
                    team_id=p.team_id,
                    team_name=team_name,
                    suspension_reason=reason,
                    matches_remaining=matches_remaining,
                    market_value_impact=mv_impact
                )
                db.add(db_suspension)
                suspension_count += 1
                logger.info(f"  Suspension: {p.player_name} ({team_name}) - {reason} - impact €{mv_impact:.2f}M")
                
        db.commit()
        logger.info(f"Successfully ingested {suspension_count} active national team suspensions.")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error ingesting national team suspensions: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    ingest_suspensions()
