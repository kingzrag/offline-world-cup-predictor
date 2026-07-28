from fastapi import APIRouter, Depends, Query, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import timezone

from database.connection import get_db
from models import Prediction
from services.prediction_service import PredictionService
from services.collection_service import CollectionService
from utils.logger import logger

router = APIRouter(prefix="/predictions", tags=["Predictions"])

prediction_service = PredictionService()
collection_service = CollectionService()

@router.get("")
def read_matches_predictions(
    competition_id: Optional[int] = Query(None, description="Filter predictions by Competition ID"),
    competition_code: Optional[str] = Query(None, description="Filter predictions by Competition Code (e.g. PL, PD, SA)"),
    db: Session = Depends(get_db)
):
    """
    Retrieves match win/draw probability projections.
    """
    logger.info("Executing GET /predictions query...")
    query = db.query(Prediction)
    
    if competition_id:
        query = query.join(Prediction.match).filter(Prediction.match.has(competition_id=competition_id))

    if competition_code:
        query = query.join(Prediction.match).filter(Prediction.match.has(Competition.code == competition_code.upper()))

    predictions = query.order_by(Prediction.created_at.desc()).all()

    results = []
    for pred in predictions:
        is_finished = pred.match.status == "FINISHED"
        if is_finished:
            winner = pred.match.winner or "DRAW"
            if winner == "HOME_TEAM":
                pred_outcome = "HOME_WIN"
                pred_winner = pred.match.home_team.name
                home_p, draw_p, away_p = 1.0, 0.0, 0.0
            elif winner == "AWAY_TEAM":
                pred_outcome = "AWAY_WIN"
                pred_winner = pred.match.away_team.name
                home_p, draw_p, away_p = 0.0, 0.0, 1.0
            else:
                pred_outcome = "DRAW"
                pred_winner = "DRAW"
                home_p, draw_p, away_p = 0.0, 1.0, 0.0
        else:
            pred_outcome = pred.predicted_outcome
            pred_winner = pred.predicted_winner.name if pred.predicted_winner else "DRAW"
            home_p, draw_p, away_p = pred.home_probability, pred.draw_probability, pred.away_probability

        results.append({
            "id": pred.id,
            "match": {
                "id": pred.match.id,
                "utc_date": pred.match.utc_date.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
                "home_team": pred.match.home_team.name,
                "away_team": pred.match.away_team.name,
                "status": pred.match.status,
                "competition_code": pred.match.competition.code if pred.match.competition else None,
                "competition_name": pred.match.competition.name if pred.match.competition else None,
            },
            "predicted_outcome": pred_outcome,
            "predicted_winner": pred_winner,
            "probabilities": {
                "home_win": home_p,
                "away_win": away_p,
                "draw": draw_p
            },
            "model_version": "actual_result_override" if is_finished else pred.model_version,
            "actual_result": pred.actual_result,
            "is_correct": pred.is_correct,
            "calculated_at": pred.updated_at.isoformat() if pred.updated_at else None
        })

    return results

@router.get("/accuracy-summary")
def get_prediction_accuracy_summary(db: Session = Depends(get_db)):
    """
    Returns total correct, total incorrect, and accuracy rate across all evaluated historical predictions.
    """
    total_evaluated = db.query(Prediction).filter(Prediction.is_correct.isnot(None)).count()
    correct_count = db.query(Prediction).filter(Prediction.is_correct == True).count()
    incorrect_count = db.query(Prediction).filter(Prediction.is_correct == False).count()
    accuracy_rate = (correct_count / total_evaluated * 100) if total_evaluated > 0 else 0.0

    return {
        "total_evaluated": total_evaluated,
        "correct_predictions": correct_count,
        "incorrect_predictions": incorrect_count,
        "accuracy_rate_percent": round(accuracy_rate, 2)
    }

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
    competition_code: str = Query("PL", description="League code to sync (e.g. PL, PD, SA, BL1, FL1, CL, WC)"),
    db: Session = Depends(get_db)
):
    """
    Orchestrates live synchronization of sports API records to local database.
    """
    try:
        summary = await collection_service.ingest_football_data(db, competition_code)
        prediction_service.generate_predictions_for_fixtures(db)

        return {
            "status": "success",
            "message": "Data ingestion and predictive updates completed successfully.",
            "ingestion_summary": summary
        }
    except Exception as e:
        logger.error(f"Collection job failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Data collection pipeline failed: {str(e)}")
