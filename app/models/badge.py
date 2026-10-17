import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class Badge(Base):
    __tablename__ = "badges"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(String(255), nullable=False)
    icon = Column(String(64), default="trophy", nullable=False)

    users = relationship("UserBadge", back_populates="badge")

class UserBadge(Base):
    __tablename__ = "user_badges"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    badge_id = Column(String(36), ForeignKey("badges.id", ondelete="CASCADE"), nullable=False)
    awarded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'badge_id', name='uq_user_badge'),
    )

    user = relationship("User", back_populates="badges")
    badge = relationship("Badge", back_populates="users")
