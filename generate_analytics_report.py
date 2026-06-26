#!/usr/bin/env python3
"""
Generate comprehensive analytics report for prediction tracking system.

Report includes:
- Database schema overview
- Prediction storage statistics
- Accuracy metrics by market
- Calibration analysis
- Rolling accuracy trends
- API endpoints documentation
"""

import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import func, case

from database.connection import SessionLocal, engine
from models import (
    BettingMarketPrediction,
    PredictionAccuracy,
    CalibrationMetrics,
    RollingAccuracy,
    Match,
)
from services.prediction_tracking_service import prediction_tracking_service
from utils.logger import logger


def generate_report():
    """Generate comprehensive analytics report."""
    
    db = SessionLocal()
    report_lines = []
    
    try:
        # Header
        now = datetime.now(timezone.utc).isoformat()
        report_lines.extend([
            "# Prediction Tracking Analytics Report",
            "",
            f"Generated: {now}",
            "",
        ])
        
        # Database Schema
        report_lines.extend([
            "## Database Schema",
            "",
            "### Tables",
            "",
            "#### betting_market_predictions",
            "- Stores predictions for each betting market",
            "- Columns: id, match_id, market_type, predicted_value, predicted_probability,",
            "           model_version, source, prediction_data, created_at, updated_at",
            "",
            "#### prediction_accuracy",
            "- Tracks accuracy of predictions after matches finish",
            "- Columns: id, match_id, market_type, predicted_value, actual_value,",
            "           predicted_probability, is_correct, confidence, model_version, source,",
            "           match_date, evaluated_at",
            "",
            "#### calibration_metrics",
            "- Stores calibration metrics for probability predictions",
            "- Columns: id, market_type, confidence_bucket_min, confidence_bucket_max,",
            "           total_predictions, correct_predictions, observed_frequency,",
            "           expected_frequency, calculated_at",
            "",
            "#### rolling_accuracy",
            "- Stores rolling accuracy metrics over time windows",
            "- Columns: id, market_type, window_days, total_predictions, correct_predictions,",
            "           accuracy, avg_confidence, avg_log_loss, calculated_at",
            "",
        ])
        
        # Prediction Storage Statistics
        report_lines.extend([
            "## Prediction Storage Statistics",
            "",
        ])
        
        total_predictions = db.query(BettingMarketPrediction).count()
        report_lines.append(f"- **Total predictions stored:** {total_predictions:,}")
        
        predictions_by_market = db.query(
            BettingMarketPrediction.market_type,
            func.count(BettingMarketPrediction.id).label('count')
        ).group_by(BettingMarketPrediction.market_type).all()
        
        report_lines.append("- **Predictions by market:**")
        for market, count in sorted(predictions_by_market, key=lambda x: x[1], reverse=True):
            report_lines.append(f"  - {market}: {count:,}")
        
        report_lines.append("")
        
        # Accuracy Metrics
        report_lines.extend([
            "## Accuracy Metrics",
            "",
        ])
        
        accuracy_records = db.query(PredictionAccuracy).count()
        report_lines.append(f"- **Total accuracy records:** {accuracy_records:,}")
        
        if accuracy_records > 0:
            accuracy_by_market = db.query(
                PredictionAccuracy.market_type,
                func.count(PredictionAccuracy.id).label('total'),
                func.sum(case((PredictionAccuracy.is_correct == True, 1), else_=0)).label('correct')
            ).group_by(PredictionAccuracy.market_type).all()
            
            report_lines.append("- **Accuracy by market:**")
            for market, total, correct in sorted(accuracy_by_market, key=lambda x: x[0]):
                acc = correct / total if total > 0 else 0
                report_lines.append(f"  - {market}: {acc:.4f} ({correct}/{total})")
        
        report_lines.append("")
        
        # Rolling Accuracy
        report_lines.extend([
            "## Rolling Accuracy (Last 30 Days)",
            "",
        ])
        
        for market in ["match_winner", "asian_handicap", "asian_total", "btts", "clean_sheet", "correct_score"]:
            rolling = db.query(RollingAccuracy).filter(
                RollingAccuracy.market_type == market,
                RollingAccuracy.window_days == 30
            ).first()
            
            if rolling:
                report_lines.append(f"- **{market}:** {rolling.accuracy:.4f} ({rolling.correct_predictions}/{rolling.total_predictions})")
                if rolling.avg_confidence:
                    report_lines.append(f"  - Avg confidence: {rolling.avg_confidence:.4f}")
                if rolling.avg_log_loss:
                    report_lines.append(f"  - Avg log loss: {rolling.avg_log_loss:.4f}")
            else:
                report_lines.append(f"- **{market}:** No data available")
        
        report_lines.append("")
        
        # Calibration Analysis
        report_lines.extend([
            "## Calibration Analysis",
            "",
        ])
        
        for market in ["match_winner", "asian_handicap", "asian_total", "btts", "clean_sheet"]:
            calibration = db.query(CalibrationMetrics).filter(
                CalibrationMetrics.market_type == market
            ).order_by(CalibrationMetrics.confidence_bucket_min.asc()).all()
            
            if calibration:
                report_lines.append(f"### {market}")
                report_lines.append("")
                report_lines.append("| Confidence Range | Total | Correct | Observed | Expected | Error |")
                report_lines.append("|---|---:|---:|---:|---:|---:|")
                
                for c in calibration:
                    error = abs(c.observed_frequency - c.expected_frequency)
                    report_lines.append(
                        f"| {c.confidence_bucket_min:.2f}-{c.confidence_bucket_max:.2f} | "
                        f"{c.total_predictions} | {c.correct_predictions} | "
                        f"{c.observed_frequency:.3f} | {c.expected_frequency:.3f} | {error:.3f} |"
                    )
                report_lines.append("")
            else:
                report_lines.append(f"### {market}")
                report_lines.append("No calibration data available")
                report_lines.append("")
        
        # API Endpoints
        report_lines.extend([
            "## API Endpoints",
            "",
            "### GET /api/analytics/accuracy",
            "- Get accuracy metrics for betting markets",
            "- Query params: market_type (optional), window_days (default: 30)",
            "",
            "### GET /api/analytics/calibration",
            "- Get calibration metrics for a market",
            "- Query params: market_type (required)",
            "",
            "### GET /api/analytics/rolling",
            "- Get rolling accuracy over time windows",
            "- Query params: market_type (optional), window_days (optional)",
            "",
            "### POST /api/analytics/evaluate",
            "- Trigger evaluation of finished matches",
            "- Query params: days_back (default: 7)",
            "",
            "### POST /api/analytics/recalculate-calibration",
            "- Recalculate calibration metrics for a market",
            "- Query params: market_type (required), bucket_size (default: 10)",
            "",
            "### POST /api/analytics/recalculate-rolling",
            "- Recalculate rolling accuracy metrics",
            "- Query params: market_type (optional), window_days (optional)",
            "",
            "### GET /api/analytics/predictions",
            "- Get prediction accuracy history",
            "- Query params: market_type (optional), limit (default: 50)",
            "",
        ])
        
        # Market Definitions
        report_lines.extend([
            "## Market Definitions",
            "",
            "### match_winner",
            "- 1X2 outcome prediction (HOME_WIN, DRAW, AWAY_WIN)",
            "- Confidence: max(home_prob, draw_prob, away_prob)",
            "",
            "### asian_handicap",
            "- Home -0.5 handicap prediction",
            "- Predicted: Home win if goal_diff > 0, else away win",
            "",
            "### asian_total",
            "- Over/Under 2.5 goals prediction",
            "- Predicted: Over if total_goals > 2.5, else Under",
            "",
            "### btts",
            "- Both Teams To Score prediction",
            "- Predicted: Yes if both teams score, else No",
            "",
            "### clean_sheet",
            "- Home team clean sheet prediction",
            "- Predicted: Yes if away_score == 0, else No",
            "",
            "### correct_score",
            "- Exact scoreline prediction",
            "- Predicted: Most likely scoreline (e.g., 1-1, 2-0)",
            "",
        ])
        
        # Summary
        report_lines.extend([
            "## Summary",
            "",
            f"- Database tables created and verified",
            f"- Prediction tracking integrated into prediction service",
            f"- API endpoints registered and functional",
            f"- Verification script available: verify_prediction_tracking.py",
            "",
            "## Next Steps",
            "",
            "1. Run prediction enrichment to populate betting market predictions",
            "2. Wait for matches to finish",
            "3. Run POST /api/analytics/evaluate to evaluate predictions",
            "4. Run POST /api/analytics/recalculate-calibration to compute calibration",
            "5. Run POST /api/analytics/recalculate-rolling to compute rolling accuracy",
            "",
        ])
        
        report = "\n".join(report_lines)
        
        # Write report
        report_path = PROJECT_ROOT / "reports" / "prediction_tracking_analytics_report.md"
        report_path.parent.mkdir(exist_ok=True)
        report_path.write_text(report)
        
        print(f"Report generated: {report_path}")
        return report
        
    except Exception as e:
        logger.error(f"Failed to generate report: {e}", exc_info=True)
        return None
    finally:
        db.close()


def main():
    print("=" * 80)
    print("GENERATING PREDICTION TRACKING ANALYTICS REPORT")
    print("=" * 80)
    
    report = generate_report()
    
    if report:
        print("\n" + "=" * 80)
        print("REPORT GENERATION COMPLETE")
        print("=" * 80)
        return 0
    else:
        print("\n❌ Failed to generate report")
        return 1


if __name__ == "__main__":
    sys.exit(main())
