import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Match(Base):
    __tablename__ = "matches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tournament_id = Column(String(36), ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False)
    round_number = Column(Integer, default=1, nullable=False)
    match_number = Column(Integer, default=1, nullable=False)
    player1_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    player2_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    winner_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(32), default="pending", nullable=False, index=True)
    # pending, scheduled, in_progress, completed, disputed, forfeited, bye
    reporting_deadline = Column(DateTime, nullable=True)
    next_match_id = Column(String(36), ForeignKey("matches.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    tournament = relationship("Tournament", back_populates="matches")
    player1 = relationship("User", foreign_keys=[player1_id])
    player2 = relationship("User", foreign_keys=[player2_id])
    winner = relationship("User", foreign_keys=[winner_id])
    
    events = relationship("MatchResultEvent", back_populates="match", cascade="all, delete-orphan", order_by="MatchResultEvent.created_at")
    reports = relationship("MatchReport", back_populates="match", cascade="all, delete-orphan")
    evidence = relationship("MatchEvidence", back_populates="match", cascade="all, delete-orphan")
    disputes = relationship("Dispute", back_populates="match", cascade="all, delete-orphan")

class MatchResultEvent(Base):
    """
    Append-only log of match outcomes.
    Never edited or deleted. Corrections create new rows referencing prior_event_id.
    """
    __tablename__ = "match_result_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    match_id = Column(String(36), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)
    prior_event_id = Column(String(36), ForeignKey("match_result_events.id", ondelete="SET NULL"), nullable=True)
    acting_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    outcome = Column(String(64), nullable=False)  # player1_win, player2_win, draw, forfeit_player1, forfeit_player2, bye
    winner_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    score_p1 = Column(Integer, default=0)
    score_p2 = Column(Integer, default=0)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    match = relationship("Match", back_populates="events")
    acting_user = relationship("User", foreign_keys=[acting_user_id])
    prior_event = relationship("MatchResultEvent", remote_side=[id])

class MatchReport(Base):
    __tablename__ = "match_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    match_id = Column(String(36), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)
    reporting_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    claimed_winner_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    score_p1 = Column(Integer, default=0)
    score_p2 = Column(Integer, default=0)
    game_link = Column(String(255), nullable=True)
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    match = relationship("Match", back_populates="reports")
    reporting_user = relationship("User", foreign_keys=[reporting_user_id])
    claimed_winner = relationship("User", foreign_keys=[claimed_winner_id])

class MatchEvidence(Base):
    __tablename__ = "match_evidence"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    match_id = Column(String(36), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(64), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    match = relationship("Match", back_populates="evidence")
    user = relationship("User", foreign_keys=[user_id])
