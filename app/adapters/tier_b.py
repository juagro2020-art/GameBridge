from typing import List, Optional
from app.adapters.base import BaseGameAdapter, ExternalRatingResult, VerificationResult

class TierBMobileGameAdapter(BaseGameAdapter):
    """
    Tier B Configurable Mobile Title Adapter.
    Framework for screenshot-reviewed mobile games (e.g. Mobile Legends / local mobile titles).
    Remains disabled by default until specific game and rules are configured.
    """
    def __init__(self, title_name: str = "Mobile Title (Unconfigured)", is_active: bool = False):
        self._title_name = title_name
        self._is_active = is_active

    @property
    def key(self) -> str:
        return "tier_b"

    @property
    def display_name(self) -> str:
        return self._title_name

    @property
    def tier(self) -> str:
        return "B"

    @property
    def supported_modes(self) -> List[str]:
        return ["standard"]

    @property
    def is_enabled(self) -> bool:
        return self._is_active

    async def fetch_rating(self, username: str, mode: str) -> Optional[ExternalRatingResult]:
        # Tier B has no direct public API; ratings are maintained via platform Elo or manual screenshot audit
        return None

    async def verify_owner(self, username: str, expected_code: str) -> VerificationResult:
        if not self._is_active:
            return VerificationResult(
                is_verified=False,
                error_message="Tier B mobile game is currently disabled pending game selection."
            )
        return VerificationResult(
            is_verified=False,
            error_message="Tier B verification requires Hub Captain screenshot review."
        )
