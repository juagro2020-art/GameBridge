import httpx
from typing import List, Optional, Dict, Any
from app.adapters.base import BaseGameAdapter, ExternalRatingResult, VerificationResult
from app.config import settings
from app.utils.logger import logger

class ChessComAdapter(BaseGameAdapter):
    @property
    def key(self) -> str:
        return "chess_com"

    @property
    def display_name(self) -> str:
        return "Chess.com"

    @property
    def tier(self) -> str:
        return "A"

    @property
    def supported_modes(self) -> List[str]:
        return ["rapid", "blitz", "bullet"]

    def _get_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": settings.CHESS_COM_USER_AGENT,
            "Accept": "application/json"
        }

    async def fetch_rating(self, username: str, mode: str) -> Optional[ExternalRatingResult]:
        clean_user = username.lower().strip()
        url = f"{settings.CHESS_COM_API_BASE}/player/{clean_user}/stats"
        try:
            async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
                resp = await client.get(url, headers=self._get_headers())
                if resp.status_code == 404:
                    logger.warning(f"Chess.com stats for {clean_user} not found")
                    return None
                resp.raise_for_status()
                stats = resp.json()

            # Chess.com stats modes: chess_rapid, chess_blitz, chess_bullet
            mode_key = f"chess_{mode}" if not mode.startswith("chess_") else mode
            mode_data = stats.get(mode_key, {})
            last_record = mode_data.get("last", {})
            rating = float(last_record.get("rating", 1200.0))
            
            record = mode_data.get("record", {})
            win = record.get("win", 0)
            loss = record.get("loss", 0)
            draw = record.get("draw", 0)
            total_games = win + loss + draw
            provisional = total_games < 20

            return ExternalRatingResult(
                game_key=self.key,
                username=clean_user,
                mode=mode,
                rating=rating,
                games_played=total_games,
                provisional=provisional,
                raw_data=stats
            )
        except Exception as e:
            logger.error(f"Chess.com API fetch error for {clean_user}: {e}")
            return None

    async def verify_owner(self, username: str, expected_code: str) -> VerificationResult:
        clean_user = username.lower().strip()
        url = f"{settings.CHESS_COM_API_BASE}/player/{clean_user}"
        try:
            async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
                resp = await client.get(url, headers=self._get_headers())
                if resp.status_code == 404:
                    return VerificationResult(is_verified=False, error_message=f"Chess.com user '{username}' not found.")
                resp.raise_for_status()
                profile = resp.json()

            # Location, status, or name fields
            bio = profile.get("location", "") + " " + profile.get("name", "") + " " + profile.get("status", "")
            if expected_code.upper() in bio.upper():
                return VerificationResult(is_verified=True, evidence_found=bio)
            else:
                return VerificationResult(
                    is_verified=False,
                    evidence_found=bio,
                    error_message=f"Verification code '{expected_code}' not found in Chess.com profile."
                )
        except Exception as e:
            return VerificationResult(is_verified=False, error_message=f"Chess.com API error: {str(e)}")
