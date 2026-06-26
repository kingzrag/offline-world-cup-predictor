"""
API routes for prediction analytics and tracking.

Endpoints:
- GET /api/analytics/accuracy - Get accuracy metrics for betting markets
- GET /api/analytics/calibration - Get calibration metrics
- GET /api/analytics/rolling - Get rolling accuracy over time windows
- POST /api/analytics/evaluate - Trigger evaluation of finished matches
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


@router.get("/accuracy")
def get_accuracy_metrics(
    market_type: Optional[str] = Query(None, description="Market type filter"),
    window_days: int = Query(30, ge=1, le=365, description="Time window in days"),
    db: Session = Depends(get_db),
):
    """
    Get accuracy metrics for betting markets.

    Returns accuracy summary for each market type over the specified time window.
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

    Returns confidence bucket metrics showing predicted vs observed frequencies.
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

    Returns accuracy for 30, 90, and 365 day windows.
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

    if not metrics:
        raise HTTPException(
            status_code=404,
            detail="No rolling accuracy metrics found"
        )

    # Group by market type
    grouped = {}
    for m in metrics:
        if m.market_type not in grouped:
            grouped[m.market_type] = []
        grouped[m.market_type].append({
            "window_days": m.window_days,
            "total_predictions": m.total_predictions,
            "correct_predictions": m.correct_predictions,
            "accuracy": m.accuracy,
            "avg_confidence": m.avg_confidence,
            "avg_log_loss": m.avg_log_loss,
            "calculated_at": m.calculated_at.isoformat() if m.calculated_at else None,
        })

    return {
        "status": "success",
        "metrics": grouped,
    }


@router.post("/evaluate")
def evaluate_finished_matches(
    days_back: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    db: Session = Depends(get_db),
):
    """
    Trigger evaluation of finished matches.

    Compares stored predictions with actual results for matches that finished
    within the specified time window.
    """
    since = datetime.now(timezone.utc) - timezone.timedelta(days=days_back)
    
    evaluated = prediction_tracking_service.evaluate_finished_matches(db, since)
    
    return {
        "status": "success",
        "evaluated_matches": evaluated,
        "since": since.isoformat(),
    }


@router.post("/recalculate-calibration")
def recalculate_calibration(
    market_type: str = Query(..., description="Market type"),
    bucket_size: int = Query(10, ge=5, le=20, description="Number of confidence buckets"),
    db: Session = Depends(get_db),
):
    """
    Recalculate calibration metrics for a market.

    Deletes old calibration data and computes new metrics based on all
    historical accuracy records.
    """
    try:
        metrics = prediction_tracking_service.compute_calibration_metrics(
            db, market_type, bucket_size
        )
        
        return {
            "status": "success",
            "market_type": market_type,
            "buckets_created": len(metrics),
        }
    except Exception as e:
        logger.error(f"Failed to recalculate calibration: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recalculate-rolling")
def recalculate_rolling_accuracy(
    market_type: Optional[str] = Query(None, description="Market type (all if not specified)"),
    window_days: Optional[int] = Query(None, ge=1, le=365, description="Specific window"),
    db: Session = Depends(get_db),
):
    """
    Recalculate rolling accuracy metrics.

    Computes rolling accuracy for specified market(s) and window(s).
    """
    market_types = [market_type] if market_type else [
        "match_winner",
        "asian_handicap",
        "asian_total",
        "btts",
        "clean_sheet",
        "correct_score",
    ]
    
    windows = [window_days] if window_days else [30, 90, 365]
    
    results = []
    for mt in market_types:
        for wd in windows:
            try:
                rolling = prediction_tracking_service.compute_rolling_accuracy(db, mt, wd)
                if rolling:
                    results.append({
                        "market_type": mt,
                        "window_days": wd,
                        "accuracy": rolling.accuracy,
                    })
            except Exception as e:
                logger.error(f"Failed to recalculate rolling accuracy for {mt} ({wd} days): {e}")
    
    return {
        "status": "success",
        "calculated": len(results),
        "results": results,
    }


@router.get("/predictions")
def get_prediction_history(
    market_type: Optional[str] = Query(None, description="Market type filter"),
    limit: int = Query(50, ge=1, le=500, description="Max records to return"),
    db: Session = Depends(get_db),
):
    """
    Get prediction accuracy history.

    Returns historical prediction accuracy records.
    """
    query = db.query(PredictionAccuracy)
    
    if market_type:
        query = query.filter(PredictionAccuracy.market_type == market_type)
    
    records = query.order_by(PredictionAccuracy.evaluated_at.desc()).limit(limit).all()
    
    return {
        "status": "success",
        "count": len(records),
        "records": [
            {
                "match_id": r.match_id,
                "market_type": r.market_type,
                "predicted_value": r.predicted_value,
                "actual_value": r.actual_value,
                "is_correct": r.is_correct,
                "confidence": r.confidence,
                "model_version": r.model_version,
                "source": r.source,
                "match_date": r.match_date.isoformat() if r.match_date else None,
                "evaluated_at": r.evaluated_at.isoformat() if r.evaluated_at else None,
            }
            for r in records
        ],
    }
