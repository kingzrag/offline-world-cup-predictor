from sqlalchemy import Column, Integer, String, Float, DateTime, UniqueConstraint
from database.base import Base
from datetime import datetime

class BookmakerOdds(Base):
    __tablename__ = "bookmaker_odds"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, nullable=False)
    sport = Column(String, nullable=False)
    bookmaker = Column(String, nullable=False)
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    home_odds = Column(Float, nullable=False)
    draw_odds = Column(Float, nullable=True)
    away_odds = Column(Float, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint("match_id", "bookmaker", name="uq_match_bookmaker"),)
