from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from database.base import Base

class TeamElo(Base):
    __tablename__ = "team_elo"

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_name = Column(String, unique=True, index=True, nullable=False)
    elo_rating = Column(Integer, nullable=False)
    country = Column(String, nullable=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
