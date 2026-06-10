from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from database.connection import get_db
from models import Team, Standing
from utils.logger import logger

router = APIRouter(prefix="/teams", tags=["Teams"])

@router.get("")
def read_teams(
    competition_id: Optional[int] = Query(None, description="Filter teams by Competition ID"),
    search: Optional[str] = Query(None, description="Search team by name substring"),
    db: Session = Depends(get_db)
):
    """
    Retrieves football teams including details of home venues and founding dates.
    """
    logger.info("Executing GET /teams query filters...")
    
    if competition_id:
        # Search via standings table for teams playing in this competition
        standings = db.query(Standing).filter(Standing.competition_id == competition_id).all()
        team_ids = [s.team_id for s in standings]
        query = db.query(Team).filter(Team.id.in_(team_ids))
    else:
        query = db.query(Team)

    if search:
        query = query.filter(Team.name.ilike(f"%{search}%") | Team.short_name.ilike(f"%{search}%"))

    teams = query.order_by(Team.name.asc()).all()

    return [
        {
            "id": t.id,
            "api_id": t.api_id,
            "name": t.name,
            "short_name": t.short_name,
            "tla": t.tla,
            "crest_url": t.crest_url,
            "founded": t.founded,
            "venue": t.venue
        }
        for t in teams
    ]

@router.get("/{team_id}")
def read_team_details(team_id: int, db: Session = Depends(get_db)):
    """
    Detailed team profile along with full roster list.
    """
    t = db.query(Team).filter(Team.id == team_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Team not found.")

    return {
        "id": t.id,
        "api_id": t.api_id,
        "name": t.name,
        "short_name": t.short_name,
        "tla": t.tla,
        "crest_url": t.crest_url,
        "founded": t.founded,
        "venue": t.venue,
        "players": [
            {
                "id": p.id,
                "name": p.name,
                "position": p.position,
                "nationality": p.nationality,
                "role": p.role
            }
            for p in t.players
        ]
    }
