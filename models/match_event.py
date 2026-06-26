from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Enum
from sqlalchemy.orm import relationship
from database.base import Base
import enum


class EventType(str, enum.Enum):
    GOAL = "goal"
    PENALTY_GOAL = "penalty_goal"
    OWN_GOAL = "own_goal"
    YELLOW_CARD = "yellow_card"
    SECOND_YELLOW_CARD = "second_yellow_card"
    RED_CARD = "red_card"
    SUBSTITUTION = "substitution"
    INJURY = "injury"
    VAR_CHECK = "var_check"


class MatchEvent(Base):
    __tablename__ = "match_events"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Event details
    type = Column(Enum(EventType), nullable=False, index=True)
    minute = Column(Integer, nullable=False, index=True)
    extra_minute = Column(Integer, nullable=True)
    description = Column(String(255), nullable=True)
    
    # Player details
    player_name = Column(String(100), nullable=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="SET NULL"), nullable=True)
    assist_player_name = Column(String(100), nullable=True)
    assist_player_id = Column(Integer, ForeignKey("players.id", ondelete="SET NULL"), nullable=True)
    
    # Substitution specific
    substitute_in_player_name = Column(String(100), nullable=True)
    substitute_in_player_id = Column(Integer, ForeignKey("players.id", ondelete="SET NULL"), nullable=True)
    
    # SofaScore specific
    sofa_score_id = Column(String(50), unique=True, nullable=True, index=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    match = relationship("Match", back_populates="events")
    team = relationship("Team")
    player = relationship("Player", foreign_keys=[player_id])
    assist_player = relationship("Player", foreign_keys=[assist_player_id])
    substitute_in_player = relationship("Player", foreign_keys=[substitute_in_player_id])
