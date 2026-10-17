from typing import Tuple
from app.config import settings

def calculate_expected_score(rating_a: float, rating_b: float) -> float:
    """Calculate expected probability of player A defeating player B."""
    return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))

def get_k_factor(matches_played: int) -> int:
    """K-factor: 40 for first 10 matches, 24 thereafter."""
    if matches_played < settings.PROVISIONAL_MATCH_THRESHOLD:
        return settings.K_FACTOR_PROVISIONAL
    return settings.K_FACTOR_ESTABLISHED

def determine_tier(elo: float) -> str:
    """Determine competitive tier based on Elo rating."""
    if elo >= 2000:
        return "Diamond"
    elif elo >= 1700:
        return "Platinum"
    elif elo >= 1400:
        return "Gold"
    elif elo >= 1100:
        return "Silver"
    return "Bronze"

def calculate_elo_change(
    rating_a: float,
    rating_b: float,
    score_a: float,  # 1.0 = A wins, 0.5 = draw, 0.0 = B wins
    matches_a: int,
    matches_b: int
) -> Tuple[float, float, float, float]:
    """
    Computes updated Elo ratings for both players.
    Returns: (new_rating_a, new_rating_b, delta_a, delta_b)
    """
    expected_a = calculate_expected_score(rating_a, rating_b)
    expected_b = 1.0 - expected_a
    score_b = 1.0 - score_a

    k_a = get_k_factor(matches_a)
    k_b = get_k_factor(matches_b)

    delta_a = k_a * (score_a - expected_a)
    delta_b = k_b * (score_b - expected_b)

    new_rating_a = max(100.0, rating_a + delta_a)
    new_rating_b = max(100.0, rating_b + delta_b)

    return round(new_rating_a, 1), round(new_rating_b, 1), round(delta_a, 1), round(delta_b, 1)
