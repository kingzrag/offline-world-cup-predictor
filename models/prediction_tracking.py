from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func, Boolean, JSON
from sqlalchemy.orm import relationship
from database.base import Base


class BettingMarketPrediction(Base):
    """Stores predictions for specific betting markets."""
    __tablename__ = "betting_market_predictions"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Market type
    market_type = Column(String(50), nullable=False)  # asian_handicap, asian_total, btts, clean_sheet, correct_score
    
    # Prediction values
    predicted_value = Column(String(50), nullable=True)  # For discrete predictions (e.g., "1-0" for correct score)
    predicted_probability = Column(Float, nullable=True)  # For binary predictions (e.g., 0.75 for BTTS Yes)
    
    # Model info
    model_version = Column(String(50), nullable=False)
    source = Column(String(50), nullable=False)  # ml_model or poisson_fallback
    
    # Raw prediction data (for flexibility)
    prediction_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    match = relationship("Match")


class PredictionAccuracy(Base):
    """Tracks accuracy of predictions after matches finish."""
    __tablename__ = "prediction_accuracy"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Market type
    market_type = Column(String(50), nullable=False)
    
    # Prediction vs actual
    predicted_value = Column(String(50), nullable=True)
    actual_value = Column(String(50), nullable=True)
    predicted_probability = Column(Float, nullable=True)
    
    # Accuracy result
    is_correct = Column(Boolean, nullable=False)
    confidence = Column(Float, nullable=True)  # Prediction confidence
    
    # Model info
    model_version = Column(String(50), nullable=False)
    source = Column(String(50), nullable=False)
    
    # Timestamps
    match_date = Column(DateTime, nullable=False)
    evaluated_at = Column(DateTime, server_default=func.now())

    # Relationships
    match = relationship("Match")


class CalibrationMetrics(Base):
    """Stores calibration metrics for probability predictions."""
    __tablename__ = "calibration_metrics"

    id = Column(Integer, primary_key=True, index=True)
    market_type = Column(String(50), nullable=False, index=True)
    
    # Confidence bucket (e.g., 0.7-0.8)
    confidence_bucket_min = Column(Float, nullable=False)
    confidence_bucket_max = Column(Float, nullable=False)
    
    # Metrics
    total_predictions = Column(Integer, nullable=False)
    correct_predictions = Column(Integer, nullable=False)
    observed_frequency = Column(Float, nullable=False)  # actual accuracy in this bucket
    expected_frequency = Column(Float, nullable=False)  # average predicted probability
    
    # Timestamp
    calculated_at = Column(DateTime, server_default=func.now(), index=True)


class RollingAccuracy(Base):
    """Stores rolling accuracy metrics over different time windows."""
    __tablename__ = "rolling_accuracy"

    id = Column(Integer, primary_key=True, index=True)
    market_type = Column(String(50), nullable=False, index=True)
    
    # Time window
    window_days = Column(Integer, nullable=False)  # 30, 90, 365
    
    # Metrics
    total_predictions = Column(Integer, nullable=False)
    correct_predictions = Column(Integer, nullable=False)
    accuracy = Column(Float, nullable=False)
    
    # Additional metrics
    avg_confidence = Column(Float, nullable=True)
    avg_log_loss = Column(Float, nullable=True)
    
    # Timestamp
    calculated_at = Column(DateTime, server_default=func.now(), index=True)


class HistoricalPredictionRecord(Base):
    """
    Permanent immutable record of predictions for completed matches.
    Used for historical accuracy auditing and performance analytics.
    """
    __tablename__ = "prediction_history"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)
    
    competition_code = Column(String(20), nullable=False, index=True)
    competition_name = Column(String(100), nullable=False)
    home_team = Column(String(100), nullable=False)
    away_team = Column(String(100), nullable=False)
    
    predicted_outcome = Column(String(50), nullable=False) # HOME_WIN, AWAY_WIN, DRAW
    home_probability = Column(Float, nullable=False)
    draw_probability = Column(Float, nullable=False)
    away_probability = Column(Float, nullable=False)
    prediction_probability = Column(Float, nullable=False) # Highest win/draw probability confidence
    
    expected_home_goals = Column(Float, nullable=True)
    expected_away_goals = Column(Float, nullable=True)
    
    actual_result = Column(String(50), nullable=False)     # HOME_WIN, AWAY_WIN, DRAW
    actual_home_score = Column(Integer, nullable=False)
    actual_away_score = Column(Integer, nullable=False)
    is_correct = Column(Boolean, nullable=False, index=True)
    
    match_date = Column(DateTime, nullable=False, index=True)
    recorded_at = Column(DateTime, server_default=func.now(), index=True)

    # Relationship
    match = relationship("Match")
