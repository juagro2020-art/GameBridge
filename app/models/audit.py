import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(64), nullable=False, index=True)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(String(64), nullable=True)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = relationship("User", foreign_keys=[user_id])

class DemoDataset(Base):
    __tablename__ = "demo_datasets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(64), default="default_demo_v1", nullable=False)
    description = Column(String(255), nullable=True)
    seeded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
