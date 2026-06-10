from fastapi import APIRouter, Depends, Query, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from database.connection import get_db
from models import Prediction
from services.prediction_service import PredictionService
from services.collection_service import CollectionService
from utils.logger import logger

router = APIRouter(prefix="/predictions", tags=["Predictions"])

prediction_service = PredictionService()
collection_service = CollectionService()

@router.get("")
def read_predictions(
    competition_id: Optional[int] = Query(None, description="Filter predictions by Competition ID"),
    db: Session = Depends(get_db)
):
    """
    Retrieves match win/draw probability projections.
    """
    logger.info("Executing GET /predictions query...")
    query = db.query(Prediction)
    
    if competition_id:
        query = query.join(Prediction.match).filter(Prediction.match.has(competition_id=competition_id))

    predictions = query.order_by(Prediction.created_at.desc()).all()

    return [
        {
            "id": pred.id,
            "match": {
                "id": pred.match.id,
                "utc_date": pred.match.utc_date.isoformat(),
                "home_team": pred.match.home_team.name,
                "away_team": pred.match.away_team.name,
                "status": pred.match.status
            },
            "predicted_outcome": pred.predicted_outcome,
            "predicted_winner": pred.predicted_winner.name if pred.predicted_winner else "DRAW",
            "probabilities": {
                "home_win": pred.home_probability,
                "away_win": pred.away_probability,
                "draw": pred.draw_probability
            },
            "model_version": pred.model_version,
            "calculated_at": pred.updated_at.isoformat()
        }
        for pred in predictions
    ]

@router.post("/trigger")
def trigger_predictions(
    competition_id: Optional[int] = Query(None, description="Specify Competition ID to narrow calculation scope"),
    db: Session = Depends(get_db)
):
    """
    Synchronously triggers the prediction engine to evaluate upcoming fixtures.
    """
    try:
        preds = prediction_service.generate_predictions_for_fixtures(db, competition_id)
        return {
            "status": "success",
            "message": f"Successfully calculated predictions for {len(preds)} fixtures.",
            "predictions_count": len(preds)
        }
    except Exception as e:
        logger.error(f"Failed prediction calculation request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction calculations failed: {str(e)}")

@router.post("/collect")
async def trigger_collection(
    competition_code: str = Query("PL", description="League code to sync (default: PL for Premier League)"),
    db: Session = Depends(get_db)
):
    """
    Orchestrates live synchronization of sports API records to local PostgreSQL database.
    """
    try:
        summary = await collection_service.ingest_football_data(db, competition_code)
        
        # After collection finishes, automatically trigger predictions update!
        prediction_service.generate_predictions_for_fixtures(db)

        return {
            "status": "success",
            "message": "Data ingestion and predictive updates completed successfully.",
            "ingestion_summary": summary
        }
    except Exception as e:
        logger.error(f"Collection job failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Data collection pipeline failed: {str(e)}")
