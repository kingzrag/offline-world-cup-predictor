from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Text
from sqlalchemy.orm import relationship
from database.base import Base


class MatchLineup(Base):
    __tablename__ = "match_lineups"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Lineup details
    formation = Column(String(20), nullable=True)
    starting_xi = Column(Text, nullable=True)  # JSON array of player IDs/names
    substitutes = Column(Text, nullable=True)  # JSON array of player IDs/names
    coach_name = Column(String(100), nullable=True)
    
    # SofaScore specific
    sofa_score_id = Column(String(50), nullable=True, index=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    match = relationship("Match", back_populates="lineups")
    team = relationship("Team")
