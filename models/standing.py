from sqlalchemy import Column, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from database.base import Base

class Standing(Base):
    __tablename__ = "standings"

    id = Column(Integer, primary_key=True, index=True)
    competition_id = Column(Integer, ForeignKey("competitions.id", ondelete="CASCADE"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    position = Column(Integer, nullable=False)
    played_games = Column(Integer, nullable=False, default=0)
    won = Column(Integer, nullable=False, default=0)
    draw = Column(Integer, nullable=False, default=0)
    lost = Column(Integer, nullable=False, default=0)
    points = Column(Integer, nullable=False, default=0)
    goals_for = Column(Integer, nullable=False, default=0)
    goals_against = Column(Integer, nullable=False, default=0)
    goals_difference = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    competition = relationship("Competition", back_populates="standings")
    team = relationship("Team", back_populates="standings")
