from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from database.base import Base


class MatchStatistic(Base):
    __tablename__ = "match_statistics"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(
        Integer,
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

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

    # Extended stats — added by FBref / StatsBomb / API-Football providers
    home_passes = Column(Integer, nullable=True)
    away_passes = Column(Integer, nullable=True)
    home_successful_passes = Column(Integer, nullable=True)
    away_successful_passes = Column(Integer, nullable=True)
    home_pass_accuracy = Column(Float, nullable=True)  # 0–100 %
    away_pass_accuracy = Column(Float, nullable=True)  # 0–100 %
    home_tackles = Column(Integer, nullable=True)
    away_tackles = Column(Integer, nullable=True)
    home_interceptions = Column(Integer, nullable=True)
    away_interceptions = Column(Integer, nullable=True)
    home_aerial_duels = Column(Integer, nullable=True)
    away_aerial_duels = Column(Integer, nullable=True)
    home_pressures = Column(Integer, nullable=True)
    away_pressures = Column(Integer, nullable=True)
    home_carries = Column(Integer, nullable=True)
    away_carries = Column(Integer, nullable=True)

    # Which provider populated this row
    data_source = Column(String(50), nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    match = relationship("Match", back_populates="statistics")
