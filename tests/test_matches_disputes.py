import pytest
from pathlib import Path
from datetime import datetime, timedelta
from sqlalchemy import select
from app.models.match import Match, MatchResultEvent, MatchReport, MatchEvidence
from app.models.dispute import Dispute
from app.models.hub import Hub, HubMembership
from app.services.user_service import UserService
from app.services.tournament_service import TournamentService
from app.services.match_service import MatchService
from app.services.dispute_service import DisputeService
from app.auth.session import create_session_token

@pytest.mark.asyncio
async def test_screenshot_match_agreement_and_append_only_event(db_session):
    p1 = await UserService.register_user(db_session, "player_alpha", "Player Alpha")
    p2 = await UserService.register_user(db_session, "player_beta", "Player Beta")

    tourney = await TournamentService.create_tournament(
        db=db_session,
        name="Screenshot Cup",
        game_key="tier_b",
        mode="standard",
        city="Addis Ababa",
        start_time=datetime.utcnow() + timedelta(hours=2),
        registration_deadline=datetime.utcnow() + timedelta(hours=1),
        max_participants=4
    )
    await TournamentService.register_player(db_session, tourney.id, p1.id)
    await TournamentService.register_player(db_session, tourney.id, p2.id)
    matches = await TournamentService.start_and_generate_bracket(db_session, tourney.id)
    m = [match for match in matches if match.player1_id and match.player2_id][0]

    # Player 1 reports Player 1 won
    p1_score = (1, 0) if m.player1_id == p1.id else (0, 1)
    res1 = await MatchService.submit_screenshot_report(
        db=db_session, match_id=m.id, user_id=p1.id, claimed_winner_id=p1.id, score_p1=p1_score[0], score_p2=p1_score[1]
    )
    assert res1["success"] is True

    # Player 2 agrees that Player 1 won
    res2 = await MatchService.submit_screenshot_report(
        db=db_session, match_id=m.id, user_id=p2.id, claimed_winner_id=p1.id, score_p1=p1_score[0], score_p2=p1_score[1]
    )
    assert res2["success"] is True

    # Match should now be completed with Player 1 as winner
    await db_session.refresh(m)
    assert m.status == "completed"
    assert m.winner_id == p1.id

    # Append-only result event must exist
    ev_stmt = select(MatchResultEvent).where(MatchResultEvent.match_id == m.id)
    events = (await db_session.execute(ev_stmt)).scalars().all()
    assert len(events) == 1
    assert events[0].winner_id == p1.id

@pytest.mark.asyncio
async def test_screenshot_conflict_opens_dispute_and_captain_resolves(db_session):
    p1 = await UserService.register_user(db_session, "user_x", "User X")
    p2 = await UserService.register_user(db_session, "user_y", "User Y")
    capt = await UserService.register_user(db_session, "capt_test", "Captain Test", role="hub_captain")

    tourney = await TournamentService.create_tournament(
        db=db_session,
        name="Dispute Cup",
        game_key="tier_b",
        mode="standard",
        city="Addis Ababa",
        start_time=datetime.utcnow() + timedelta(hours=2),
        registration_deadline=datetime.utcnow() + timedelta(hours=1),
        max_participants=4
    )
    await TournamentService.register_player(db_session, tourney.id, p1.id)
    await TournamentService.register_player(db_session, tourney.id, p2.id)
    matches = await TournamentService.start_and_generate_bracket(db_session, tourney.id)
    m = [match for match in matches if match.player1_id and match.player2_id][0]

    # Player 1 claims Player 1 won
    p1_score = (1, 0) if m.player1_id == p1.id else (0, 1)
    await MatchService.submit_screenshot_report(
        db=db_session, match_id=m.id, user_id=p1.id, claimed_winner_id=p1.id, score_p1=p1_score[0], score_p2=p1_score[1]
    )
    # Player 2 conflicts, claims Player 2 won!
    p2_score = (1, 0) if m.player1_id == p2.id else (0, 1)
    res_conflict = await MatchService.submit_screenshot_report(
        db=db_session, match_id=m.id, user_id=p2.id, claimed_winner_id=p2.id, score_p1=p2_score[0], score_p2=p2_score[1]
    )
    assert "dispute" in res_conflict["message"].lower()

    # Match status should be disputed
    await db_session.refresh(m)
    assert m.status == "disputed"

    disp_stmt = select(Dispute).where(Dispute.match_id == m.id)
    dispute = (await db_session.execute(disp_stmt)).scalar_one_or_none()
    assert dispute is not None
    assert dispute.status == "open"

    # Hub Captain resolves dispute confirming Player 1
    resolve_res = await DisputeService.resolve_dispute(
        db=db_session,
        dispute_id=dispute.id,
        captain_id=capt.id,
        decision="confirm_p1",
        reason="Reviewed screenshot proof: Player 1 won 1-0."
    )
    assert resolve_res["success"] is True
    with pytest.raises(ValueError, match="already been resolved"):
        await DisputeService.resolve_dispute(
            db=db_session,
            dispute_id=dispute.id,
            captain_id=capt.id,
            decision="confirm_p1",
            reason="Duplicate resolution attempt."
        )

    # Verify match completed and append-only event recorded
    await db_session.refresh(m)
    assert m.status == "completed"
    assert m.winner_id == m.player1_id

    ev_stmt = select(MatchResultEvent).where(MatchResultEvent.match_id == m.id)
    events = (await db_session.execute(ev_stmt)).scalars().all()
    assert len(events) == 1
    assert "Captain decision" in events[0].reason

@pytest.mark.asyncio
async def test_nonparticipant_cannot_submit_match_report(db_session):
    p1 = await UserService.register_user(db_session, "report_p1", "Report Player One")
    p2 = await UserService.register_user(db_session, "report_p2", "Report Player Two")
    outsider = await UserService.register_user(db_session, "report_other", "Report Outsider")
    tourney = await TournamentService.create_tournament(
        db=db_session,
        name="Report Permission Cup",
        game_key="tier_b",
        mode="standard",
        city="Addis Ababa",
        start_time=datetime.utcnow() + timedelta(hours=2),
        registration_deadline=datetime.utcnow() + timedelta(hours=1),
        max_participants=4
    )
    await TournamentService.register_player(db_session, tourney.id, p1.id)
    await TournamentService.register_player(db_session, tourney.id, p2.id)
    matches = await TournamentService.start_and_generate_bracket(db_session, tourney.id)
    match = next(match for match in matches if match.player1_id and match.player2_id)

    result = await MatchService.submit_screenshot_report(
        db=db_session,
        match_id=match.id,
        user_id=outsider.id,
        claimed_winner_id=p1.id,
        score_p1=1,
        score_p2=0
    )

    assert not result["success"]
    reports = (await db_session.execute(select(MatchReport).where(MatchReport.match_id == match.id))).scalars().all()
    assert reports == []

@pytest.mark.asyncio
async def test_open_dispute_requires_participant_and_updates_match(db_session):
    p1 = await UserService.register_user(db_session, "dispute_p1", "Dispute Player One")
    p2 = await UserService.register_user(db_session, "dispute_p2", "Dispute Player Two")
    outsider = await UserService.register_user(db_session, "dispute_other", "Dispute Outsider")
    tourney = await TournamentService.create_tournament(
        db=db_session,
        name="Direct Dispute Cup",
        game_key="tier_b",
        mode="standard",
        city="Addis Ababa",
        start_time=datetime.utcnow() + timedelta(hours=2),
        registration_deadline=datetime.utcnow() + timedelta(hours=1),
        max_participants=4
    )
    await TournamentService.register_player(db_session, tourney.id, p1.id)
    await TournamentService.register_player(db_session, tourney.id, p2.id)
    matches = await TournamentService.start_and_generate_bracket(db_session, tourney.id)
    match = next(match for match in matches if match.player1_id and match.player2_id)

    with pytest.raises(PermissionError):
        await DisputeService.open_dispute(db_session, match.id, outsider.id, "Outside player report")

    result = await DisputeService.open_dispute(db_session, match.id, p1.id, "Opponent result differs")

    await db_session.refresh(match)
    assert result["success"]
    assert match.status == "disputed"

@pytest.mark.asyncio
async def test_evidence_view_is_limited_to_assigned_hub_captain(client, db_session, tmp_path, monkeypatch):
    player = await UserService.register_user(db_session, "evidence_player", "Evidence Player")
    captain = await UserService.register_user(db_session, "evidence_captain", "Evidence Captain", role="hub_captain")
    other_captain = await UserService.register_user(db_session, "other_captain", "Other Captain", role="hub_captain")
    hub = Hub(name="Evidence Bole Hub", slug="evidence-bole", city="Addis Ababa")
    other_hub = Hub(name="Evidence Hawassa Hub", slug="evidence-hawassa", city="Hawassa")
    db_session.add_all([hub, other_hub])
    await db_session.flush()
    db_session.add(HubMembership(user_id=captain.id, hub_id=hub.id, role="captain"))
    tournament = await TournamentService.create_tournament(
        db=db_session,
        name="Evidence Privacy Cup",
        game_key="tier_b",
        mode="standard",
        city="Addis Ababa",
        hub_id=hub.id,
        start_time=datetime.utcnow() + timedelta(hours=2),
        registration_deadline=datetime.utcnow() + timedelta(hours=1),
        max_participants=2
    )
    match = Match(
        tournament_id=tournament.id,
        round_number=1,
        match_number=1,
        player1_id=player.id,
        status="disputed"
    )
    db_session.add(match)
    await db_session.flush()
    evidence_file = tmp_path / "private.png"
    evidence_file.write_bytes(b"\x89PNG\r\n\x1a\nprivate-evidence")
    evidence = MatchEvidence(
        match_id=match.id,
        user_id=player.id,
        file_path=str(evidence_file),
        file_name="private.png",
        file_size=evidence_file.stat().st_size,
        content_type="image/png"
    )
    db_session.add(evidence)
    await db_session.commit()
    monkeypatch.setattr("app.api.matches.settings.UPLOAD_DIR", str(tmp_path))

    client.cookies.set("gb_session", create_session_token(captain.id, captain.role))
    response = await client.get(f"/api/matches/{match.id}/evidence/{evidence.id}")
    assert response.status_code == 200
    assert response.content.endswith(b"private-evidence")
    assert response.headers["cache-control"] == "private, no-store"

    client.cookies.set("gb_session", create_session_token(other_captain.id, other_captain.role))
    forbidden = await client.get(f"/api/matches/{match.id}/evidence/{evidence.id}")
    assert forbidden.status_code == 403
