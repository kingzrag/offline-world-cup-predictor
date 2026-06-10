"""
Compute total squad value for every national team by summing up its players market values.
Saves to teams.squad_market_value.
"""

import sys
import os
from sqlalchemy import text

# Add root folder to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import SessionLocal
from models import Team, NationalTeamPlayer
from utils.logger import logger

def compute_market_values():
    db = SessionLocal()
    try:
        logger.info("Computing total squad market values for national teams...")
        
        # Query total market value per team
        results = db.query(
            NationalTeamPlayer.team_id,
            Team.name,
            text("SUM(national_team_players.market_value)")
        ).join(
            Team, Team.id == NationalTeamPlayer.team_id
        ).group_by(
            NationalTeamPlayer.team_id, Team.name
        ).all()
        
        updated_count = 0
        for team_id, name, total_val in results:
            if total_val is not None:
                # Update teams.squad_market_value
                db.execute(
                    text("UPDATE teams SET squad_market_value = :val WHERE id = :id"),
                    {"val": float(total_val), "id": team_id}
                )
                updated_count += 1
                logger.info(f"  {name}: squad_market_value = €{total_val:.2f}M")
                
        db.commit()
        logger.info(f"Computed and updated squad_market_value for {updated_count} national teams.")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error computing squad market values: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    compute_market_values()
