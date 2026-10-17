import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class Game(Base):
    __tablename__ = "games"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String(32), unique=True, nullable=False, index=True)  # lichess, chess_com, tier_b
    display_name = Column(String(64), nullable=False)
    tier = Column(String(8), default="A", nullable=False)  # A, B, C
    is_enabled = Column(Boolean, default=True)
    icon_url = Column(String(255), nullable=True)
    rules_json = Column(Text, nullable=True)

class GameAccount(Base):
    __tablename__ = "game_accounts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    game_key = Column(String(32), nullable=False, index=True)
    external_username = Column(String(128), nullable=False)
    status = Column(String(32), default="pending_verification", nullable=False)  
    # pending_verification, claimed, verified, rejected, revoked
    bio_code = Column(String(32), nullable=True)
    bio_code_expires_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    is_demo = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('game_key', 'external_username', name='uq_game_external_username'),
        UniqueConstraint('user_id', 'game_key', name='uq_user_game_key'),
    )

    user = relationship("User", back_populates="game_accounts")
    verifications = relationship("AccountVerification", back_populates="game_account", cascade="all, delete-orphan")
    snapshots = relationship("RatingSnapshot", back_populates="game_account", cascade="all, delete-orphan")

class AccountVerification(Base):
    __tablename__ = "account_verifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    game_account_id = Column(String(36), ForeignKey("game_accounts.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(32), nullable=False)
    status = Column(String(32), default="pending", nullable=False)  # pending, verified, failed
    attempts = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    checked_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    game_account = relationship("GameAccount", back_populates="verifications")
