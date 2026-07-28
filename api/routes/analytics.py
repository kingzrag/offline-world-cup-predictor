"""
API routes for prediction analytics and tracking.

Endpoints:
- GET /api/analytics/overall - Overall model accuracy and totals
- GET /api/analytics/by-league - Accuracy breakdown per competition
- GET /api/analytics/monthly - Monthly accuracy trends
- GET /api/analytics/by-outcome - Home Win, Draw, Away Win accuracy
- GET /api/analytics/markets - BTTS and Over/Under market accuracy
- GET /api/analytics/recent - Recent evaluated predictions feed
- GET /api/analytics/accuracy - Legacy betting market accuracy
- POST /api/analytics/evaluate - Trigger manual evaluation of finished matches
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database.connection import get_db
from models import PredictionAccuracy, CalibrationMetrics, RollingAccuracy
from services.prediction_tracking_service import prediction_tracking_service
from utils.logger import logger

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


# ── NEW DEDICATED PREDICTION HISTORY ANALYTICS ENDPOINTS ──────────────────────

@router.get("/overall")
def get_overall_accuracy(db: Session = Depends(get_db)):
    """
    Returns overall model accuracy, total predictions evaluated, correct & incorrect count.
    """
    logger.info("Executing GET /api/analytics/overall query...")
    return prediction_tracking_service.get_overall_accuracy_analytics(db)


@router.get("/by-league")
def get_league_accuracy(db: Session = Depends(get_db)):
    """
    Returns prediction accuracy breakdown for every competition.
    """
    logger.info("Executing GET /api/analytics/by-league query...")
    return prediction_tracking_service.get_league_accuracy_analytics(db)


@router.get("/monthly")
def get_monthly_accuracy(db: Session = Depends(get_db)):
    """
    Returns monthly accuracy trends (YYYY-MM).
    """
    logger.info("Executing GET /api/analytics/monthly query...")
    return prediction_tracking_service.get_monthly_accuracy_analytics(db)


@router.get("/by-outcome")
def get_outcome_accuracy(db: Session = Depends(get_db)):
    """
    Returns breakdown accuracy for Home Win, Draw, and Away Win predictions.
    """
    logger.info("Executing GET /api/analytics/by-outcome query...")
    return prediction_tracking_service.get_outcome_accuracy_analytics(db)


@router.get("/markets")
def get_market_accuracy(db: Session = Depends(get_db)):
    """
    Returns accuracy metrics for BTTS and Over/Under 2.5 betting markets.
    """
    logger.info("Executing GET /api/analytics/markets query...")
    return prediction_tracking_service.get_market_accuracy_analytics(db)


@router.get("/recent")
def get_recent_historical_predictions(
    limit: int = Query(50, ge=1, le=500, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    Returns paginated feed of recently evaluated historical predictions.
    """
    logger.info(f"Executing GET /api/analytics/recent query (limit={limit}, offset={offset})...")
    return prediction_tracking_service.get_recent_historical_predictions(db, limit=limit, offset=offset)


# ── EXISTING / LEGACY ANALYTICS ENDPOINTS ──────────────────────────────────────

@router.get("/accuracy")
def get_accuracy_metrics(
    market_type: Optional[str] = Query(None, description="Market type filter"),
    window_days: int = Query(30, ge=1, le=365, description="Time window in days"),
    db: Session = Depends(get_db),
):
    """
    Get accuracy metrics for betting markets.
    """
    market_types = [market_type] if market_type else [
        "match_winner",
        "asian_handicap",
        "asian_total",
        "btts",
        "clean_sheet",
        "correct_score",
    ]

    results = []
    for mt in market_types:
        summary = prediction_tracking_service.get_market_accuracy_summary(db, mt, window_days)
        results.append(summary)

    return {
        "status": "success",
        "window_days": window_days,
        "metrics": results,
    }


@router.get("/calibration")
def get_calibration_metrics(
    market_type: str = Query(..., description="Market type"),
    db: Session = Depends(get_db),
):
    """
    Get calibration metrics for a market.
    """
    metrics = (
        db.query(CalibrationMetrics)
        .filter(CalibrationMetrics.market_type == market_type)
        .order_by(CalibrationMetrics.confidence_bucket_min.asc())
        .all()
    )

    if not metrics:
        raise HTTPException(
            status_code=404,
            detail=f"No calibration metrics found for market: {market_type}"
        )

    return {
        "status": "success",
        "market_type": market_type,
        "calculated_at": metrics[0].calculated_at.isoformat() if metrics[0].calculated_at else None,
        "buckets": [
            {
                "confidence_range": f"{m.confidence_bucket_min:.2f}-{m.confidence_bucket_max:.2f}",
                "total_predictions": m.total_predictions,
                "correct_predictions": m.correct_predictions,
                "observed_frequency": m.observed_frequency,
                "expected_frequency": m.expected_frequency,
                "calibration_error": abs(m.observed_frequency - m.expected_frequency),
            }
            for m in metrics
        ],
    }


@router.get("/rolling")
def get_rolling_accuracy(
    market_type: Optional[str] = Query(None, description="Market type filter"),
    window_days: Optional[int] = Query(None, ge=1, le=365, description="Specific window"),
    db: Session = Depends(get_db),
):
    """
    Get rolling accuracy metrics over different time windows.
    """
    query = db.query(RollingAccuracy)
    
    if market_type:
        query = query.filter(RollingAccuracy.market_type == market_type)
    
    if window_days:
        query = query.filter(RollingAccuracy.window_days == window_days)
    
    metrics = query.order_by(
        RollingAccuracy.market_type,
        RollingAccuracy.window_days
    ).all()

    return {
        "status": "success",
        "metrics": [
            {
                "market_type": m.market_type,
                "window_days": m.window_days,
                "total_predictions": m.total_predictions,
                "correct_predictions": m.correct_predictions,
                "accuracy": m.accuracy,
                "avg_confidence": m.avg_confidence,
                "avg_log_loss": m.avg_log_loss,
                "calculated_at": m.calculated_at.isoformat() if m.calculated_at else None,
            }
            for m in metrics
        ],
    }


@router.post("/evaluate")
def trigger_evaluation(
    days: int = Query(7, ge=1, le=365, description="Days to look back for finished matches"),
    db: Session = Depends(get_db),
):
    """
    Trigger evaluation of finished matches and compute metrics.
    """
    try:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        evaluated_count = prediction_tracking_service.evaluate_finished_matches(db, since=since)
        
        for market_type in prediction_tracking_service.MARKET_TYPES:
            try:
                prediction_tracking_service.compute_calibration_metrics(db, market_type)
                for window in [30, 90, 365]:
                    prediction_tracking_service.compute_rolling_accuracy(db, market_type, window)
            except Exception as e:
                logger.warning(f"Failed to compute metrics for {market_type}: {e}")

        return {
            "status": "success",
            "message": f"Successfully evaluated {evaluated_count} finished matches",
            "evaluated_count": evaluated_count,
        }
    except Exception as e:
        logger.error(f"Failed evaluation job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Evaluation job failed: {str(e)}")
