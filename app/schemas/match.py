from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class MatchResultSubmit(BaseModel):
    match_id: str
    winner_id: str
    score_p1: int = Field(0, ge=0, le=99)
    score_p2: int = Field(0, ge=0, le=99)
    game_link: Optional[str] = None
    comments: Optional[str] = None

class DisputeCreate(BaseModel):
    match_id: str
    reason: str = Field(..., min_length=5)

class DisputeResolve(BaseModel):
    dispute_id: str
    decision: str  # confirm_p1, confirm_p2, draw, forfeit_p1, forfeit_p2
    reason: str = Field(..., min_length=5)

class FairPlaySubmit(BaseModel):
    match_id: str
    target_user_id: str
    rating: str  # clean, suspicious
    notes: Optional[str] = None
