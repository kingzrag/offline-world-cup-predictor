from sqlalchemy import Column, Integer, String, Date, DateTime, Float, ForeignKey, func, Enum
from sqlalchemy.orm import relationship
from database.base import Base
from models.suspension_history import SuspensionStatus


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
    
    # SofaScore specific
    sofa_score_id = Column(String(50), nullable=True, index=True)
    source = Column(String(50), nullable=True, default="unknown")
    status = Column(Enum(SuspensionStatus), nullable=True, default=SuspensionStatus.OFFICIAL)
    matches_banned = Column(Integer, nullable=True)
    reason = Column(String(255), nullable=True)
    official_date = Column(Date, nullable=True)

    # Relationships
    team = relationship("Team", back_populates="suspensions")
    history = relationship("SuspensionHistory", back_populates="suspension", cascade="all, delete-orphan")
