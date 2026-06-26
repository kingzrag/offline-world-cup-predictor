from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from database.base import Base


class MatchStatistic(Base):
    __tablename__ = "match_statistics"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Possession (0-100)
    home_possession = Column(Float, nullable=True)
    away_possession = Column(Float, nullable=True)
    
    # Shots
    home_shots = Column(Integer, nullable=True, default=0)
    away_shots = Column(Integer, nullable=True, default=0)
    home_shots_on_target = Column(Integer, nullable=True, default=0)
    away_shots_on_target = Column(Integer, nullable=True, default=0)
    
    # Corners
    home_corners = Column(Integer, nullable=True, default=0)
    away_corners = Column(Integer, nullable=True, default=0)
    
    # Expected goals (xG)
    home_expected_goals = Column(Float, nullable=True)
    away_expected_goals = Column(Float, nullable=True)
    
    # Additional stats
    home_fouls = Column(Integer, nullable=True, default=0)
    away_fouls = Column(Integer, nullable=True, default=0)
    home_offsides = Column(Integer, nullable=True, default=0)
    away_offsides = Column(Integer, nullable=True, default=0)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    match = relationship("Match", back_populates="statistics")
