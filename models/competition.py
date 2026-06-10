from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from database.base import Base

class Competition(Base):
    __tablename__ = "competitions"

    id = Column(Integer, primary_key=True, index=True)
    api_id = Column(String(50), unique=True, index=True, nullable=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), nullable=True)
    area = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    matches = relationship("Match", back_populates="competition", cascade="all, delete-orphan")
    standings = relationship("Standing", back_populates="competition", cascade="all, delete-orphan")
