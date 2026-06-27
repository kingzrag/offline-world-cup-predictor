from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from database.connection import get_db
from models import Injury, Player
from utils.logger import logger

router = APIRouter(prefix="/injuries", tags=["Injuries"])

@router.get("")
def read_injuries(
    team_id: Optional[int] = Query(None, description="Filter injuries by Team ID"),
    player_id: Optional[int] = Query(None, description="Filter injuries by Player ID"),
    status: Optional[str] = Query(None, description="Filter injuries by status (e.g. Injured, Recovering, Questionable)"),
    db: Session = Depends(get_db)
):
    """
    Retrieves current active injury table records.
    """
    logger.info("Executing GET /injuries query filters...")
    query = db.query(Injury).options(joinedload(Injury.team))

    if team_id:
        query = query.filter(Injury.team_id == team_id)
        
    if player_id:
        player_db = db.query(Player).filter(Player.id == player_id).first()
        if player_db:
            query = query.filter(Injury.player_name == player_db.name, Injury.team_id == player_db.team_id)
        else:
            return []

    injuries = query.all()

    response = []
    for inj in injuries:
        # Try to resolve local player info
        player_db = db.query(Player).filter_by(team_id=inj.team_id, name=inj.player_name).first()
        player_info = {
            "id": player_db.id if player_db else None,
            "name": player_db.name if player_db else inj.player_name,
            "position": player_db.position if player_db else "Unknown"
        }
        
        response.append({
            "id": inj.id,
            "player": player_info,
            "team": {
                "id": inj.team.id,
                "name": inj.team.name
            },
            "description": inj.injury_type,
            "status": "Injured",
            "expected_return": inj.expected_return_date.isoformat() if inj.expected_return_date else None
        })

    return response
