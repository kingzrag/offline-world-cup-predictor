from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from database.connection import get_db
from models import Player
from utils.logger import logger

router = APIRouter(prefix="/players", tags=["Players"])

@router.get("")
def read_players(
    team_id: Optional[int] = Query(None, description="Filter players by Team ID"),
    position: Optional[str] = Query(None, description="Filter players by position (e.g. Goalkeeper, Defender, Midfielder, Attacker)"),
    nationality: Optional[str] = Query(None, description="Filter players by nationality"),
    db: Session = Depends(get_db)
):
    """
    Retrieves squad players with filters.
    """
    logger.info("Executing GET /players query filters...")
    query = db.query(Player)

    if team_id:
        query = query.filter(Player.team_id == team_id)
        
    if position:
        query = query.filter(Player.position.ilike(position))
        
    if nationality:
        query = query.filter(Player.nationality.ilike(nationality))

    players = query.order_by(Player.name.asc()).all()

    return [
        {
            "id": p.id,
            "api_id": p.api_id,
            "name": p.name,
            "position": p.position,
            "date_of_birth": p.date_of_birth.isoformat() if p.date_of_birth else None,
            "nationality": p.nationality,
            "role": p.role,
            "team": {
                "id": p.team.id,
                "name": p.team.name
            }
        }
        for p in players
    ]
