import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Dispute(Base):
    __tablename__ = "disputes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    match_id = Column(String(36), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)
    opened_by_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(32), default="open", nullable=False, index=True)  # open, under_review, resolved, rejected
    reason = Column(Text, nullable=False)
    captain_decision = Column(Text, nullable=True)
    resolved_by_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    match = relationship("Match", back_populates="disputes")
    opened_by = relationship("User", foreign_keys=[opened_by_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])

class FairPlayFeedback(Base):
    __tablename__ = "fair_play_feedbacks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    match_id = Column(String(36), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    submitter_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating = Column(String(32), default="clean", nullable=False)  # clean, suspicious
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    submitter = relationship("User", foreign_keys=[submitter_id])
    target_user = relationship("User", foreign_keys=[target_user_id])
