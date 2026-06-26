# Prediction Tracking Analytics Report

Generated: 2026-06-26T20:37:49.959673+00:00

## Database Schema

### Tables

#### betting_market_predictions
- Stores predictions for each betting market
- Columns: id, match_id, market_type, predicted_value, predicted_probability,
           model_version, source, prediction_data, created_at, updated_at

#### prediction_accuracy
- Tracks accuracy of predictions after matches finish
- Columns: id, match_id, market_type, predicted_value, actual_value,
           predicted_probability, is_correct, confidence, model_version, source,
           match_date, evaluated_at

#### calibration_metrics
- Stores calibration metrics for probability predictions
- Columns: id, market_type, confidence_bucket_min, confidence_bucket_max,
           total_predictions, correct_predictions, observed_frequency,
           expected_frequency, calculated_at

#### rolling_accuracy
- Stores rolling accuracy metrics over time windows
- Columns: id, market_type, window_days, total_predictions, correct_predictions,
           accuracy, avg_confidence, avg_log_loss, calculated_at

## Prediction Storage Statistics

- **Total predictions stored:** 0
- **Predictions by market:**

## Accuracy Metrics

- **Total accuracy records:** 0

## Rolling Accuracy (Last 30 Days)

- **match_winner:** No data available
- **asian_handicap:** No data available
- **asian_total:** No data available
- **btts:** No data available
- **clean_sheet:** No data available
- **correct_score:** No data available

## Calibration Analysis

### match_winner
No calibration data available

### asian_handicap
No calibration data available

### asian_total
No calibration data available

### btts
No calibration data available

### clean_sheet
No calibration data available

## API Endpoints

### GET /api/analytics/accuracy
- Get accuracy metrics for betting markets
- Query params: market_type (optional), window_days (default: 30)

### GET /api/analytics/calibration
- Get calibration metrics for a market
- Query params: market_type (required)

### GET /api/analytics/rolling
- Get rolling accuracy over time windows
- Query params: market_type (optional), window_days (optional)

### POST /api/analytics/evaluate
- Trigger evaluation of finished matches
- Query params: days_back (default: 7)

### POST /api/analytics/recalculate-calibration
- Recalculate calibration metrics for a market
- Query params: market_type (required), bucket_size (default: 10)

### POST /api/analytics/recalculate-rolling
- Recalculate rolling accuracy metrics
- Query params: market_type (optional), window_days (optional)

### GET /api/analytics/predictions
- Get prediction accuracy history
- Query params: market_type (optional), limit (default: 50)

## Market Definitions

### match_winner
- 1X2 outcome prediction (HOME_WIN, DRAW, AWAY_WIN)
- Confidence: max(home_prob, draw_prob, away_prob)

### asian_handicap
- Home -0.5 handicap prediction
- Predicted: Home win if goal_diff > 0, else away win

### asian_total
- Over/Under 2.5 goals prediction
- Predicted: Over if total_goals > 2.5, else Under

### btts
- Both Teams To Score prediction
- Predicted: Yes if both teams score, else No

### clean_sheet
- Home team clean sheet prediction
- Predicted: Yes if away_score == 0, else No

### correct_score
- Exact scoreline prediction
- Predicted: Most likely scoreline (e.g., 1-1, 2-0)

## Summary

- Database tables created and verified
- Prediction tracking integrated into prediction service
- API endpoints registered and functional
- Verification script available: verify_prediction_tracking.py

## Next Steps

1. Run prediction enrichment to populate betting market predictions
2. Wait for matches to finish
3. Run POST /api/analytics/evaluate to evaluate predictions
4. Run POST /api/analytics/recalculate-calibration to compute calibration
5. Run POST /api/analytics/recalculate-rolling to compute rolling accuracy
