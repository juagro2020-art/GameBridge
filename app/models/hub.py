import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Hub(Base):
    __tablename__ = "hubs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(128), unique=True, nullable=False)
    slug = Column(String(128), unique=True, nullable=False, index=True)
    city = Column(String(64), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    is_demo = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    memberships = relationship("HubMembership", back_populates="hub", cascade="all, delete-orphan")
    tournaments = relationship("Tournament", back_populates="hub")

class HubMembership(Base):
    __tablename__ = "hub_memberships"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    hub_id = Column(String(36), ForeignKey("hubs.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(32), default="player", nullable=False)  # player, captain
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="hub_memberships")
    hub = relationship("Hub", back_populates="memberships")
