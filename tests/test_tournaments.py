import pytest
from datetime import datetime, timedelta
from app.tournaments.bracket import (
    next_power_of_two,
    generate_standard_seeding_pairs,
    build_single_elimination_bracket
)
from app.services.tournament_service import TournamentService
from app.services.user_service import UserService

def test_next_power_of_two():
    assert next_power_of_two(2) == 2
    assert next_power_of_two(3) == 4
    assert next_power_of_two(4) == 4
    assert next_power_of_two(5) == 8
    assert next_power_of_two(8) == 8
    assert next_power_of_two(9) == 16

def test_seeding_pairs():
    # 8 players: standard 1 vs 8, 4 vs 5, 2 vs 7, 3 vs 6
    pairs = generate_standard_seeding_pairs(8)
    assert len(pairs) == 4
    assert (1, 8) in pairs
    assert (2, 7) in pairs

def test_bracket_with_byes_odd_count():
    # 5 players => bracket size 8 (3 Byes)
    players = ["p1", "p2", "p3", "p4", "p5"]
    matches = build_single_elimination_bracket(players)
    
    # 8-bracket has 7 matches total: 4 in R1, 2 in R2, 1 in R3
    assert len(matches) == 7

    # Round 1 matches
    r1 = [m for m in matches if m["round_number"] == 1]
    assert len(r1) == 4

    # Top seed p1 should have a bye (matched against seed 8 which is None)
    bye_matches = [m for m in r1 if m["is_bye"]]
    assert len(bye_matches) == 3
    # In bye matches, the present player is automatically winner
    for bm in bye_matches:
        assert bm["status"] == "completed"
        assert bm["winner_id"] is not None

    # Round 2 matches should have bye winners pre-advanced
    r2 = [m for m in matches if m["round_number"] == 2]
    assert len(r2) == 2

@pytest.mark.asyncio
async def test_tournament_service_registration_and_bracket(db_session):
    u1 = await UserService.register_user(db_session, "player_one", "Player One")
    u2 = await UserService.register_user(db_session, "player_two", "Player Two")
    u3 = await UserService.register_user(db_session, "player_three", "Player Three")

    tourney = await TournamentService.create_tournament(
        db=db_session,
        name="Test Cup",
        game_key="lichess",
        mode="rapid",
        city="Addis Ababa",
        start_time=datetime.utcnow() + timedelta(hours=2),
        registration_deadline=datetime.utcnow() + timedelta(hours=1),
        max_participants=8
    )

    # Register players
    await TournamentService.register_player(db_session, tourney.id, u1.id)
    await TournamentService.register_player(db_session, tourney.id, u2.id)
    await TournamentService.register_player(db_session, tourney.id, u3.id)

    # Prevent duplicate registration
    with pytest.raises(ValueError, match="already registered"):
        await TournamentService.register_player(db_session, tourney.id, u1.id)

    # Start tournament and verify seeded bracket
    matches = await TournamentService.start_and_generate_bracket(db_session, tourney.id)
    assert len(matches) == 3  # 4-bracket (2 in R1, 1 in R2)
    assert tourney.status == "in_progress"
    with pytest.raises(ValueError, match="cannot be started"):
        await TournamentService.start_and_generate_bracket(db_session, tourney.id)
