from sqlalchemy import Column, Integer, String, Date, DateTime, Float, ForeignKey, func
from sqlalchemy.orm import relationship
from database.base import Base

class NationalTeamInjury(Base):
    __tablename__ = "national_team_injuries"

    id = Column(Integer, primary_key=True, index=True)
    player_name = Column(String(100), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    team_name = Column(String(100), nullable=False)
    injury_status = Column(String(100), nullable=True)
    injury_description = Column(String(255), nullable=True)
    expected_return_date = Column(Date, nullable=True)
    market_value_impact = Column(Float, nullable=True)  # player's market value in €M
    
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    team = relationship("Team", back_populates="national_team_injuries")
