from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from database.base import Base

class DataFreshness(Base):
    __tablename__ = "data_freshness"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, nullable=False, index=True)
    data_type = Column(String, nullable=False, index=True)
    last_successful_update = Column(DateTime(timezone=True), nullable=False)
    record_count = Column(Integer, default=0)
    oldest_record = Column(DateTime(timezone=True), nullable=True)
    newest_record = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="OK")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
