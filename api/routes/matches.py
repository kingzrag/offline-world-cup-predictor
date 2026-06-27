from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime, date, timezone

from database.connection import get_db
from models import Match
from utils.logger import logger

router = APIRouter(prefix="/matches", tags=["Matches"])

@router.get("")
def read_matches(
    competition_id: Optional[int] = Query(None, description="Filter matches by Competition ID"),
    team_id: Optional[int] = Query(None, description="Filter matches by Team ID (either Home or Away)"),
    status: Optional[str] = Query(None, description="Filter matches by status (e.g. SCHEDULED, FINISHED, IN_PLAY)"),
    from_date: Optional[date] = Query(None, description="Start date format YYYY-MM-DD"),
    to_date: Optional[date] = Query(None, description="End date format YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """
    Retrieves match fixtures with complete query filters.
    """
    logger.info("Executing GET /matches query filters...")
    query = db.query(Match).options(
        joinedload(Match.competition),
        joinedload(Match.home_team),
        joinedload(Match.away_team)
    )

    if competition_id:
        query = query.filter(Match.competition_id == competition_id)
        
    if team_id:
        query = query.filter((Match.home_team_id == team_id) | (Match.away_team_id == team_id))
        
    if status:
        query = query.filter(Match.status == status.upper())
        
    if from_date:
        query = query.filter(Match.utc_date >= datetime.combine(from_date, datetime.min.time()))
        
    if to_date:
        query = query.filter(Match.utc_date <= datetime.combine(to_date, datetime.max.time()))

    matches = query.order_by(Match.utc_date.asc()).all()
    
    return [
        {
            "id": m.id,
            "api_id": m.api_id,
            "competition": {
                "id": m.competition.id,
                "name": m.competition.name,
                "code": m.competition.code
            },
            "home_team": {
                "id": m.home_team.id,
                "name": m.home_team.name,
                "tla": m.home_team.tla,
                "crest_url": m.home_team.crest_url
            },
            "away_team": {
                "id": m.away_team.id,
                "name": m.away_team.name,
                "tla": m.away_team.tla,
                "crest_url": m.away_team.crest_url
            },
            "utc_date": m.utc_date.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            "status": m.status,
            "stage": m.stage,
            "group": m.group,
            "home_score": m.home_score,
            "away_score": m.away_score,
            "winner": m.winner
        }
        for m in matches
    ]
