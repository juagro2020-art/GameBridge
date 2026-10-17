import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    telegram_id = Column(Integer, unique=True, nullable=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    display_name = Column(String(128), nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=True)
    role = Column(String(32), default="player", nullable=False)  # player, hub_captain, super_admin
    city = Column(String(64), default="Addis Ababa", nullable=False)
    phone = Column(String(32), nullable=True)
    public_identifier = Column(String(64), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    is_demo = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    hub_memberships = relationship("HubMembership", back_populates="user", cascade="all, delete-orphan")
    game_accounts = relationship("GameAccount", back_populates="user", cascade="all, delete-orphan")
    platform_ratings = relationship("PlatformRating", back_populates="user", cascade="all, delete-orphan")
    tournament_participations = relationship("TournamentParticipant", back_populates="user")
    badges = relationship("UserBadge", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    language = Column(String(8), default="en", nullable=False)  # en, am, om
    notifications_enabled = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="preferences")
