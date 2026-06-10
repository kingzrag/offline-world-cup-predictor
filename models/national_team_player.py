from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from database.base import Base

class NationalTeamPlayer(Base):
    __tablename__ = "national_team_players"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    player_name = Column(String(100), nullable=False)
    position = Column(String(50), nullable=True)
    age = Column(Integer, nullable=True)
    market_value = Column(Float, nullable=True)  # in Millions of Euros (€M)
    transfermarkt_url = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    team = relationship("Team", back_populates="national_team_players")
