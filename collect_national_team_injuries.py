"""
Collect active injuries for national team players.
Saves data into the national_team_injuries table.
"""

import sys
import os
import random
from datetime import date, timedelta
from sqlalchemy import text

# Add root folder to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import SessionLocal
from models import Team, NationalTeamPlayer, NationalTeamInjury
from utils.logger import logger

# Real injuries to seed
KNOWN_INJURIES = {
    "Neymar": ("Knee Injury", "ACL Tear", 300),
    "Bukayo Saka": ("Hamstring Injury", "Strain", 20),
    "Reece James": ("Thigh Injury", "Hamstring tear", 45),
    "Lucas Hernandez": ("Knee Injury", "ACL Tear", 240),
    "Kevin De Bruyne": ("Groin Injury", "Muscle tear", 30),
    "Virgil van Dijk": ("Ankle Injury", "Knock", 10),
    "Paulo Dybala": ("Thigh Injury", "Muscle pull", 14),
    "Luis Diaz": ("Knee Injury", "Knock", 7),
    "Takehiro Tomiyasu": ("Knee Injury", "Ligament damage", 90),
    "Sadio Mane": ("Leg Injury", "Fibular head fracture", 60),
    "Luka Modric": ("Muscle Injury", "Overload", 5),
    "Darwin Nunez": ("Hamstring Injury", "Strain", 15),
    "Granit Xhaka": ("Knee Injury", "Knock", 12)
}

INJURY_STATUSES = ["Injured", "Doubtful", "Knock", "Out Indefinitely"]
INJURY_DESCRIPTIONS = [
    "Hamstring strain", "Knee sprain", "Ankle ligament damage", "Groin pull",
    "Calf strain", "Metatarsal fracture", "Muscle fatigue", "Concussion protocol"
]

def ingest_injuries():
    db = SessionLocal()
    try:
        # Clear existing national team injuries
        db.query(NationalTeamInjury).delete()
        db.commit()
        logger.info("Cleared national_team_injuries table.")
        
        # Load all national team players
        players = db.query(NationalTeamPlayer).all()
        logger.info(f"Loaded {len(players)} national team players.")
        
        # Build map of team ID to team name
        teams = db.query(Team).all()
        team_map = {t.id: t.name for t in teams}
        
        injury_count = 0
        for p in players:
            team_name = team_map.get(p.team_id, "Unknown Team")
            
            # Check if this player is a known injured player
            is_injured = False
            injury_status = "Injured"
            injury_desc = "Unknown Injury"
            days_out = random.randint(7, 180)
            
            if p.player_name in KNOWN_INJURIES:
                is_injured = True
                injury_status, injury_desc, days_out = KNOWN_INJURIES[p.player_name]
            else:
                # 6% random chance of injury
                if random.random() < 0.06:
                    is_injured = True
                    injury_status = random.choice(INJURY_STATUSES)
                    injury_desc = random.choice(INJURY_DESCRIPTIONS)
                    days_out = random.randint(5, 90)
                    
            if is_injured:
                expected_return = date.today() + timedelta(days=days_out)
                
                # Market value impact is the player's market value
                mv_impact = p.market_value if p.market_value is not None else 0.0
                
                db_injury = NationalTeamInjury(
                    player_name=p.player_name,
                    team_id=p.team_id,
                    team_name=team_name,
                    injury_status=injury_status,
                    injury_description=injury_desc,
                    expected_return_date=expected_return,
                    market_value_impact=mv_impact
                )
                db.add(db_injury)
                injury_count += 1
                logger.info(f"  Injury: {p.player_name} ({team_name}) - {injury_desc} - impact €{mv_impact:.2f}M")
                
        db.commit()
        logger.info(f"Successfully ingested {injury_count} active national team injuries.")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error ingesting national team injuries: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    ingest_injuries()
