from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.sql import func
from database.base import Base

class FeatureSnapshot(Base):
    __tablename__ = "feature_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)
    prediction_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    feature_name = Column(String, nullable=False, index=True)
    feature_value = Column(Float, nullable=False)
    source = Column(String, nullable=False)
    source_timestamp = Column(DateTime(timezone=True), nullable=True)
    model_version = Column(String, nullable=False, default="v2.0.0")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
