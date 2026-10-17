import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class RatingSnapshot(Base):
    __tablename__ = "rating_snapshots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    game_account_id = Column(String(36), ForeignKey("game_accounts.id", ondelete="CASCADE"), nullable=False)
    mode = Column(String(32), default="rapid", nullable=False)  # bullet, blitz, rapid, classical
    rating = Column(Float, nullable=False)
    games_played = Column(Integer, default=0)
    provisional = Column(Boolean, default=False)
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    game_account = relationship("GameAccount", back_populates="snapshots")

class PlatformRating(Base):
    __tablename__ = "platform_ratings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    game_key = Column(String(32), default="lichess", nullable=False)
    mode = Column(String(32), default="rapid", nullable=False)
    elo = Column(Float, default=1200.0, nullable=False, index=True)
    matches_played = Column(Integer, default=0, nullable=False)
    tier = Column(String(32), default="Bronze", nullable=False)  # Bronze, Silver, Gold, Platinum, Diamond
    is_demo = Column(Boolean, default=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'game_key', 'mode', name='uq_user_game_mode_rating'),
    )

    user = relationship("User", back_populates="platform_ratings")
