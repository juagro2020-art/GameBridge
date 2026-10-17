import pytest
from app.ratings.elo import calculate_expected_score, get_k_factor, determine_tier, calculate_elo_change

def test_expected_score():
    # Equal ratings -> 50% probability
    assert calculate_expected_score(1500, 1500) == pytest.approx(0.5, 0.01)
    # Higher rating has higher probability
    assert calculate_expected_score(1700, 1500) > 0.75
    assert calculate_expected_score(1300, 1500) < 0.25

def test_k_factors():
    # First 10 matches use K=40
    assert get_k_factor(0) == 40
    assert get_k_factor(5) == 40
    assert get_k_factor(9) == 40
    # 10 or more matches use K=24
    assert get_k_factor(10) == 24
    assert get_k_factor(25) == 24

def test_tier_determination():
    assert determine_tier(1050) == "Bronze"
    assert determine_tier(1250) == "Silver"
    assert determine_tier(1450) == "Gold"
    assert determine_tier(1750) == "Platinum"
    assert determine_tier(2050) == "Diamond"

def test_elo_calculation_provisional_win():
    # Player A (1200, 0 matches) beats Player B (1200, 0 matches)
    new_a, new_b, delta_a, delta_b = calculate_elo_change(
        rating_a=1200.0,
        rating_b=1200.0,
        score_a=1.0,
        matches_a=0,
        matches_b=0
    )
    # With K=40 and E=0.5, delta should be +20.0
    assert delta_a == 20.0
    assert delta_b == -20.0
    assert new_a == 1220.0
    assert new_b == 1180.0

def test_elo_calculation_established_win():
    # Both established (matches >= 10), K=24
    new_a, new_b, delta_a, delta_b = calculate_elo_change(
        rating_a=1500.0,
        rating_b=1500.0,
        score_a=1.0,
        matches_a=15,
        matches_b=15
    )
    assert delta_a == 12.0
    assert delta_b == -12.0
    assert new_a == 1512.0
    assert new_b == 1488.0
