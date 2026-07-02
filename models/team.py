from sqlalchemy import Column, Integer, String, DateTime, Float, func
from sqlalchemy.orm import relationship
from database.base import Base

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    api_id = Column(String(50), unique=True, index=True, nullable=True)
    name = Column(String(100), nullable=False, index=True)
    short_name = Column(String(50), nullable=True, index=True)
    tla = Column(String(10), nullable=True, index=True)
    crest_url = Column(String(255), nullable=True)
    founded = Column(Integer, nullable=True)
    venue = Column(String(100), nullable=True)
    transfermarkt_url = Column(String(255), nullable=True)
    fifa_ranking = Column(Integer, nullable=True)
    market_value = Column(Float, nullable=True)
    squad_market_value = Column(Float, nullable=True)  # Sum of national team players market value
    gender = Column(String(20), nullable=False, default="MEN", server_default="MEN")
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    players = relationship("Player", back_populates="team", cascade="all, delete-orphan")
    injuries = relationship("Injury", back_populates="team", cascade="all, delete-orphan")
    suspensions = relationship("Suspension", back_populates="team", cascade="all, delete-orphan")
    standings = relationship("Standing", back_populates="team", cascade="all, delete-orphan")
    
    # National team intelligence relationships
    national_team_players = relationship("NationalTeamPlayer", back_populates="team", cascade="all, delete-orphan")
    national_team_injuries = relationship("NationalTeamInjury", back_populates="team", cascade="all, delete-orphan")
    national_team_suspensions = relationship("NationalTeamSuspension", back_populates="team", cascade="all, delete-orphan")
    
    # Matches where this team is home or away
    home_matches = relationship("Match", foreign_keys="[Match.home_team_id]", back_populates="home_team")
    away_matches = relationship("Match", foreign_keys="[Match.away_team_id]", back_populates="away_team")
    
    # Predicted winners mapping
    predicted_wins = relationship("Prediction", back_populates="predicted_winner")
