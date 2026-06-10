from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from models.bookmaker_odds import BookmakerOdds
from utils.logger import logger

router = APIRouter(prefix="/odds", tags=["odds"])

@router.get("/")
def list_odds(db: Session = Depends(get_db)):
    """Return all stored odds records."""
    records = db.query(BookmakerOdds).all()
    logger.info(f"Returned {len(records)} odds records via API.")
    return records

@router.get("/{match_id}")
def get_odds_by_match(match_id: int, db: Session = Depends(get_db)):
    """Return odds for a specific match ID."""
    records = db.query(BookmakerOdds).filter(BookmakerOdds.match_id == match_id).all()
    if not records:
        raise HTTPException(status_code=404, detail="No odds found for the given match ID.")
    logger.info(f"Returned {len(records)} odds records for match {match_id} via API.")
    return records
