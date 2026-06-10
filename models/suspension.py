from sqlalchemy import Column, Integer, String, Date, DateTime, Float, ForeignKey, func
from sqlalchemy.orm import relationship
from database.base import Base

class Suspension(Base):
    __tablename__ = "suspensions"

    id = Column(Integer, primary_key=True, index=True)
    player_name = Column(String(100), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    team_name = Column(String(100), nullable=False)
    suspension_reason = Column(String(255), nullable=True)
    matches_remaining = Column(Integer, nullable=True)
    player_market_value = Column(Float, nullable=True)  # Player market value in €M
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    team = relationship("Team", back_populates="suspensions")
