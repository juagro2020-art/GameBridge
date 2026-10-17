import httpx
from typing import List, Optional, Dict, Any
from app.adapters.base import BaseGameAdapter, ExternalRatingResult, VerificationResult
from app.config import settings
from app.utils.logger import logger

class LichessAdapter(BaseGameAdapter):
    @property
    def key(self) -> str:
        return "lichess"

    @property
    def display_name(self) -> str:
        return "Lichess.org"

    @property
    def tier(self) -> str:
        return "A"

    @property
    def supported_modes(self) -> List[str]:
        return ["rapid", "blitz", "bullet", "classical"]

    async def fetch_rating(self, username: str, mode: str) -> Optional[ExternalRatingResult]:
        if mode not in self.supported_modes:
            mode = "rapid"
        url = f"{settings.LICHESS_API_BASE}/api/user/{username}"
        try:
            async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
                resp = await client.get(url, headers={"Accept": "application/json"})
                if resp.status_code == 404:
                    logger.warning(f"Lichess user {username} not found")
                    return None
                resp.raise_for_status()
                data = resp.json()

            perfs = data.get("perfs", {})
            perf = perfs.get(mode, {})
            rating = float(perf.get("rating", 1500.0))
            games = int(perf.get("games", 0))
            provisional = bool(perf.get("prov", False))

            return ExternalRatingResult(
                game_key=self.key,
                username=username,
                mode=mode,
                rating=rating,
                games_played=games,
                provisional=provisional,
                raw_data=data
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"Lichess HTTP error for user {username}: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Lichess API error for user {username}: {e}")
            return None

    async def verify_owner(self, username: str, expected_code: str) -> VerificationResult:
        url = f"{settings.LICHESS_API_BASE}/api/user/{username}"
        try:
            async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
                resp = await client.get(url, headers={"Accept": "application/json"})
                if resp.status_code == 404:
                    return VerificationResult(is_verified=False, error_message=f"Lichess account '{username}' does not exist.")
                resp.raise_for_status()
                data = resp.json()

            # Profile bio can be in profile.bio or bio field
            profile = data.get("profile", {})
            bio = profile.get("bio") or data.get("bio") or ""

            if expected_code.upper() in bio.upper():
                return VerificationResult(is_verified=True, evidence_found=bio)
            else:
                return VerificationResult(
                    is_verified=False,
                    evidence_found=bio,
                    error_message=f"Verification code '{expected_code}' not found in Lichess bio."
                )
        except Exception as e:
            logger.error(f"Lichess ownership verification error: {e}")
            return VerificationResult(is_verified=False, error_message=f"External API error: {str(e)}")

    async def verify_match_game(self, game_id_or_url: str, player1_username: str, player2_username: str) -> Dict[str, Any]:
        """
        Verify a completed Lichess game for tournament match reporting.
        """
        # Extract game ID if full URL was provided
        clean_id = game_id_or_url.strip()
        if "lichess.org/" in clean_id:
            clean_id = clean_id.split("lichess.org/")[1].split("/")[0].split("#")[0]
        # Clean potential 12-char game ID with move turn to 8-char base game ID
        if len(clean_id) > 8:
            clean_id = clean_id[:8]

        url = f"{settings.LICHESS_API_BASE}/game/export/{clean_id}?tags=true&clocks=false&evals=false"
        try:
            async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
                resp = await client.get(url, headers={"Accept": "application/json"})
                if resp.status_code == 404:
                    return {"valid": False, "error": f"Lichess game {clean_id} not found."}
                resp.raise_for_status()
                game = resp.json()

            players = game.get("players", {})
            white = players.get("white", {}).get("user", {}).get("name", "").lower()
            black = players.get("black", {}).get("user", {}).get("name", "").lower()

            p1 = player1_username.lower()
            p2 = player2_username.lower()

            # Verify participants match either as white/black or black/white
            if not ((white == p1 and black == p2) or (white == p2 and black == p1)):
                return {
                    "valid": False,
                    "error": f"Game participants ({white} vs {black}) do not match match players ({p1} vs {p2})."
                }

            status = game.get("status", "")
            winner_color = game.get("winner")  # "white", "black", or None for draw

            winner_username = None
            if winner_color == "white":
                winner_username = white
            elif winner_color == "black":
                winner_username = black

            return {
                "valid": True,
                "game_id": clean_id,
                "status": status,
                "winner_color": winner_color,
                "winner_username": winner_username,
                "is_draw": winner_color is None,
                "white": white,
                "black": black,
                "raw_game": game
            }
        except Exception as e:
            return {"valid": False, "error": f"Failed to verify Lichess game: {str(e)}"}
