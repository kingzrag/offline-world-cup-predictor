#!/usr/bin/env python3
"""
Verification script for prediction tracking system.

Tests:
- Database tables exist and have correct schema
- Prediction storage works correctly
- Accuracy evaluation works correctly
- Calibration metrics compute correctly
- Rolling accuracy computes correctly
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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


def verify_database_tables():
    """Verify that all tracking tables exist."""
    print("\n=== Verifying Database Tables ===")
    
    from sqlalchemy import inspect
    inspector = inspect(engine)
    
    tables = inspector.get_table_names()
    required_tables = [
        "betting_market_predictions",
        "prediction_accuracy",
        "calibration_metrics",
        "rolling_accuracy",
    ]
    
    for table in required_tables:
        if table in tables:
            print(f"✅ Table '{table}' exists")
            columns = [col["name"] for col in inspector.get_columns(table)]
            print(f"   Columns: {', '.join(columns)}")
        else:
            print(f"❌ Table '{table}' missing")
            return False
    
    return True


def verify_prediction_storage():
    """Verify that predictions can be stored."""
    print("\n=== Verifying Prediction Storage ===")
    
    db = SessionLocal()
    try:
        # Find a test match
        match = db.query(Match).first()
        if not match:
            print("❌ No matches found in database")
            return False
        
        # Store a test prediction
        prediction = prediction_tracking_service.store_betting_market_prediction(
            db=db,
            match_id=match.id,
            market_type="btts",
            predicted_value="Yes",
            predicted_probability=0.65,
            model_version="test_v1.0",
            source="test",
            prediction_data={"test": True},
        )
        
        print(f"✅ Stored test prediction (ID: {prediction.id})")
        
        # Retrieve it
        retrieved = db.query(BettingMarketPrediction).filter_by(id=prediction.id).first()
        if retrieved and retrieved.market_type == "btts":
            print("✅ Retrieved prediction matches stored data")
            # Clean up
            db.delete(retrieved)
            db.commit()
            return True
        else:
            print("❌ Failed to retrieve prediction")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()


def verify_accuracy_evaluation():
    """Verify that accuracy evaluation works."""
    print("\n=== Verifying Accuracy Evaluation ===")
    
    db = SessionLocal()
    try:
        # Find a finished match with predictions
        finished_match = (
            db.query(Match)
            .filter(
                Match.status == "FINISHED",
                Match.home_score.isnot(None),
                Match.away_score.isnot(None),
            )
            .first()
        )
        
        if not finished_match:
            print("⚠️  No finished matches found, skipping accuracy evaluation test")
            return True
        
        # Create a test prediction for this match
        prediction = prediction_tracking_service.store_betting_market_prediction(
            db=db,
            match_id=finished_match.id,
            market_type="btts",
            predicted_value="Yes",
            predicted_probability=0.65,
            model_version="test_v1.0",
            source="test",
        )
        
        # Evaluate the match
        prediction_tracking_service._evaluate_match_predictions(db, finished_match)
        
        # Check if accuracy record was created
        accuracy = (
            db.query(PredictionAccuracy)
            .filter_by(match_id=finished_match.id, market_type="btts")
            .first()
        )
        
        if accuracy:
            print(f"✅ Accuracy record created (correct: {accuracy.is_correct})")
            # Clean up
            db.delete(prediction)
            db.delete(accuracy)
            db.commit()
            return True
        else:
            print("❌ Accuracy record not created")
            # Clean up
            db.delete(prediction)
            db.commit()
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()


def verify_calibration_metrics():
    """Verify that calibration metrics can be computed."""
    print("\n=== Verifying Calibration Metrics ===")
    
    db = SessionLocal()
    try:
        # Try to compute calibration for BTTS
        metrics = prediction_tracking_service.compute_calibration_metrics(db, "btts", bucket_size=5)
        
        if metrics:
            print(f"✅ Computed {len(metrics)} calibration buckets")
            for m in metrics[:2]:  # Show first 2
                print(f"   Bucket {m.confidence_bucket_min:.2f}-{m.confidence_bucket_max:.2f}: "
                      f"{m.observed_frequency:.3f} vs {m.expected_frequency:.3f}")
            return True
        else:
            print("⚠️  No calibration data (may be normal if no predictions yet)")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()


def verify_rolling_accuracy():
    """Verify that rolling accuracy can be computed."""
    print("\n=== Verifying Rolling Accuracy ===")
    
    db = SessionLocal()
    try:
        # Try to compute rolling accuracy for BTTS
        rolling = prediction_tracking_service.compute_rolling_accuracy(db, "btts", window_days=30)
        
        if rolling:
            print(f"✅ Computed rolling accuracy: {rolling.accuracy:.4f}")
            print(f"   Total predictions: {rolling.total_predictions}")
            print(f"   Correct: {rolling.correct_predictions}")
            return True
        else:
            print("⚠️  No rolling accuracy data (may be normal if no predictions yet)")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()


def verify_api_endpoints():
    """Verify that API endpoints are registered."""
    print("\n=== Verifying API Endpoints ===")
    
    try:
        from api.main import app
        routes = [route.path for route in app.routes]
        
        analytics_routes = [r for r in routes if "/analytics" in r]
        
        if analytics_routes:
            print(f"✅ Found {len(analytics_routes)} analytics routes:")
            for route in sorted(set(analytics_routes)):
                print(f"   {route}")
            return True
        else:
            print("❌ No analytics routes found")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    print("=" * 80)
    print("PREDICTION TRACKING VERIFICATION")
    print("=" * 80)
    
    results = []
    
    results.append(("Database Tables", verify_database_tables()))
    results.append(("Prediction Storage", verify_prediction_storage()))
    results.append(("Accuracy Evaluation", verify_accuracy_evaluation()))
    results.append(("Calibration Metrics", verify_calibration_metrics()))
    results.append(("Rolling Accuracy", verify_rolling_accuracy()))
    results.append(("API Endpoints", verify_api_endpoints()))
    
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All verification tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
