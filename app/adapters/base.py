from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class ExternalRatingResult(BaseModel):
    game_key: str
    username: str
    mode: str
    rating: float
    games_played: int = 0
    provisional: bool = False
    raw_data: Optional[Dict[str, Any]] = None

class VerificationResult(BaseModel):
    is_verified: bool
    evidence_found: Optional[str] = None
    error_message: Optional[str] = None

class BaseGameAdapter(ABC):
    @property
    @abstractmethod
    def key(self) -> str:
        """Unique adapter identifier (e.g. 'lichess', 'chess_com')."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable game title."""
        pass

    @property
    @abstractmethod
    def tier(self) -> str:
        """Tier: 'A' (API-verified), 'B' (Screenshot-verified), 'C' (Platform-only)."""
        pass

    @property
    @abstractmethod
    def supported_modes(self) -> List[str]:
        """List of supported competitive game modes."""
        pass

    @abstractmethod
    async def fetch_rating(self, username: str, mode: str) -> Optional[ExternalRatingResult]:
        """Fetch player rating for given mode from external official API."""
        pass

    @abstractmethod
    async def verify_owner(self, username: str, expected_code: str) -> VerificationResult:
        """Verify account ownership through external profile evidence (e.g. bio code)."""
        pass
