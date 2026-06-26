from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from database.base import Base


class PlayerMatchPerformance(Base):
    __tablename__ = "player_match_performances"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(
        Integer,
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    team_id = Column(
        Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    player_id = Column(
        Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=True, index=True
    )
    player_name = Column(String(100), nullable=False)

    # Performance data
    rating = Column(Float, nullable=True)
    position = Column(String(50), nullable=True)
    is_starter = Column(Integer, default=0)  # 0 = substitute, 1 = starter

    # Stats
    minutes_played = Column(Integer, nullable=True)
    goals = Column(Integer, nullable=True, default=0)
    assists = Column(Integer, nullable=True, default=0)
    shots = Column(Integer, nullable=True, default=0)
    shots_on_target = Column(Integer, nullable=True, default=0)
    passes = Column(Integer, nullable=True, default=0)
    successful_passes = Column(Integer, nullable=True)
    pass_accuracy = Column(Float, nullable=True)
    tackles = Column(Integer, nullable=True, default=0)
    interceptions = Column(Integer, nullable=True, default=0)
    saves = Column(Integer, nullable=True, default=0)
    fouls_committed = Column(Integer, nullable=True, default=0)
    fouls_drawn = Column(Integer, nullable=True, default=0)
    yellow_cards = Column(Integer, nullable=True, default=0)
    red_cards = Column(Integer, nullable=True, default=0)
    offsides = Column(Integer, nullable=True, default=0)
    corners = Column(Integer, nullable=True, default=0)

    # Extended stats — added by FBref / StatsBomb providers
    aerial_duels = Column(Integer, nullable=True)
    aerial_duels_won = Column(Integer, nullable=True)
    key_passes = Column(Integer, nullable=True)
    pressures = Column(Integer, nullable=True)
    carries = Column(Integer, nullable=True)
    dribbles_completed = Column(Integer, nullable=True)
    clearances = Column(Integer, nullable=True)
    blocks = Column(Integer, nullable=True)

    # Source-specific IDs and data
    sofa_score_id = Column(String(50), nullable=True, index=True)
    sofa_score_rating = Column(Float, nullable=True)
    fbref_id = Column(String(100), nullable=True, index=True)
    statsbomb_id = Column(String(100), nullable=True, index=True)
    statsbomb_xg = Column(Float, nullable=True)  # expected goals for shots taken

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    match = relationship("Match", back_populates="player_performances")
    team = relationship("Team")
    player = relationship("Player")
