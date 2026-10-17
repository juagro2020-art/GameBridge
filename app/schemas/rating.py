from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PlatformRatingOut(BaseModel):
    game_key: str
    mode: str
    elo: float
    matches_played: int
    tier: str
    updated_at: datetime

    class Config:
        from_attributes = True

class RatingSnapshotOut(BaseModel):
    mode: str
    rating: float
    games_played: int
    provisional: bool
    recorded_at: datetime

    class Config:
        from_attributes = True
