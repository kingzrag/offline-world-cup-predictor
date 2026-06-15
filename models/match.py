from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from database.base import Base

class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    api_id = Column(String(50), unique=True, index=True, nullable=True)
    competition_id = Column(Integer, ForeignKey("competitions.id", ondelete="CASCADE"), nullable=False)
    home_team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    utc_date = Column(DateTime, nullable=False, index=True)
    status = Column(String(50), nullable=False, default="SCHEDULED")  # e.g., SCHEDULED, FINISHED, POSTPONED, IN_PLAY
    stage = Column(String(50), nullable=True)
    group = Column(String(50), nullable=True)
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    winner = Column(String(50), nullable=True)  # e.g., "HOME_TEAM", "AWAY_TEAM", "DRAW"
    live_minute = Column(Integer, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    competition = relationship("Competition", back_populates="matches")
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_matches")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_matches")
    
    predictions = relationship("Prediction", back_populates="match", cascade="all, delete-orphan")
