from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, func
from sqlalchemy.orm import relationship
from database.base import Base


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    api_id = Column(String(50), unique=True, index=True, nullable=True)
    api_football_id = Column(String(50), unique=True, index=True, nullable=True)
    sofa_score_id = Column(String(50), unique=True, index=True, nullable=True)
    competition_id = Column(Integer, ForeignKey("competitions.id", ondelete="CASCADE"), nullable=False, index=True)
    home_team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    utc_date = Column(DateTime, nullable=False, index=True)
    status = Column(String(50), nullable=False, default="SCHEDULED", index=True)  # e.g., SCHEDULED, FINISHED, POSTPONED, IN_PLAY
    stage = Column(String(50), nullable=True)
    group = Column(String(50), nullable=True)
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    winner = Column(String(50), nullable=True)  # e.g., "HOME_TEAM", "AWAY_TEAM", "DRAW"
    live_minute = Column(Integer, nullable=True)
    
    # New live fields
    current_minute = Column(Integer, nullable=True)
    home_red_cards = Column(Integer, nullable=True, default=0)
    away_red_cards = Column(Integer, nullable=True, default=0)
    home_yellow_cards = Column(Integer, nullable=True, default=0)
    away_yellow_cards = Column(Integer, nullable=True, default=0)
    current_home_score = Column(Integer, nullable=True)
    current_away_score = Column(Integer, nullable=True)
    
    # SofaScore specific fields
    home_formation = Column(String(20), nullable=True)
    away_formation = Column(String(20), nullable=True)
    home_possession = Column(Float, nullable=True)
    away_possession = Column(Float, nullable=True)
    home_expected_goals = Column(Float, nullable=True)
    away_expected_goals = Column(Float, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    competition = relationship("Competition", back_populates="matches")
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_matches")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_matches")
    
    predictions = relationship("Prediction", back_populates="match", cascade="all, delete-orphan")
    statistics = relationship("MatchStatistic", back_populates="match", cascade="all, delete-orphan", uselist=False)
    events = relationship("MatchEvent", back_populates="match", cascade="all, delete-orphan")
    player_performances = relationship("PlayerMatchPerformance", back_populates="match", cascade="all, delete-orphan")
    lineups = relationship("MatchLineup", back_populates="match", cascade="all, delete-orphan")
