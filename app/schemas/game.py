from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class GameOut(BaseModel):
    id: str
    key: str
    display_name: str
    tier: str
    is_enabled: bool
    icon_url: Optional[str] = None

    class Config:
        from_attributes = True

class GameAccountLinkRequest(BaseModel):
    game_key: str
    external_username: str
    consent: bool = False

class GameAccountOut(BaseModel):
    id: str
    game_key: str
    external_username: str
    status: str
    bio_code: Optional[str] = None
    verified_at: Optional[datetime] = None

    class Config:
        from_attributes = True
