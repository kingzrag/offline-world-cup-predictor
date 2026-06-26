from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Enum
from sqlalchemy.orm import relationship
from database.base import Base
import enum


class SuspensionStatus(str, enum.Enum):
    PENDING = "pending"
    OFFICIAL = "official"
    APPEALED = "appealed"
    RESOLVED = "resolved"


class SuspensionHistory(Base):
    __tablename__ = "suspension_history"

    id = Column(Integer, primary_key=True, index=True)
    suspension_id = Column(Integer, ForeignKey("suspensions.id", ondelete="CASCADE"), nullable=False, index=True)
    old_status = Column(Enum(SuspensionStatus), nullable=True)
    new_status = Column(Enum(SuspensionStatus), nullable=False)
    changed_by = Column(String(100), nullable=True)
    reason = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    suspension = relationship("Suspension", back_populates="history")
