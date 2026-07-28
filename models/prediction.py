from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, func
from sqlalchemy.orm import relationship
from database.base import Base

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)
    predicted_winner_id = Column(Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)
    predicted_outcome = Column(String(50), nullable=False)  # e.g., HOME_WIN, AWAY_WIN, DRAW
    home_probability = Column(Float, nullable=False)
    away_probability = Column(Float, nullable=False)
    draw_probability = Column(Float, nullable=False)
    model_version = Column(String(50), nullable=False, default="v1.0")
    expected_home_goals = Column(Float, nullable=True)
    expected_away_goals = Column(Float, nullable=True)

    # Prediction evaluation fields (populated when match finishes)
    actual_result = Column(String(50), nullable=True)     # e.g., HOME_WIN, AWAY_WIN, DRAW
    is_correct = Column(Boolean, nullable=True, index=True) # True = Prediction Correct, False = Prediction Incorrect
    finished_at = Column(DateTime, nullable=True)          # Timestamp when match ended
    evaluated_at = Column(DateTime, nullable=True)         # Timestamp when accuracy evaluation was computed

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    match = relationship("Match", back_populates="predictions")
    predicted_winner = relationship("Team", back_populates="predicted_wins")
