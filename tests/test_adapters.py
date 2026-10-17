import pytest
from unittest.mock import patch, AsyncMock
import httpx
from app.adapters.lichess import LichessAdapter
from app.adapters.chess_com import ChessComAdapter

@pytest.mark.asyncio
async def test_lichess_fetch_rating_mock():
    adapter = LichessAdapter()
    mock_payload = {
        "id": "desta_eth",
        "username": "desta_eth",
        "perfs": {
            "rapid": {"rating": 1725, "games": 88, "prov": False},
            "blitz": {"rating": 1640, "games": 120, "prov": False}
        }
    }

    mock_resp = httpx.Response(status_code=200, json=mock_payload, request=httpx.Request("GET", "https://lichess.org/api/user/desta_eth"))
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        res = await adapter.fetch_rating("desta_eth", "rapid")
        assert res is not None
        assert res.rating == 1725.0
        assert res.games_played == 88
        assert res.provisional is False

@pytest.mark.asyncio
async def test_lichess_bio_verification_success():
    adapter = LichessAdapter()
    mock_payload = {
        "username": "desta_eth",
        "profile": {"bio": "Ethiopian esports player GB-4F7K competing in GameBridge"}
    }
    mock_resp = httpx.Response(status_code=200, json=mock_payload, request=httpx.Request("GET", "https://lichess.org/api/user/desta_eth"))
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        res = await adapter.verify_owner("desta_eth", "GB-4F7K")
        assert res.is_verified is True
        assert "GB-4F7K" in res.evidence_found

@pytest.mark.asyncio
async def test_lichess_bio_verification_failure():
    adapter = LichessAdapter()
    mock_payload = {
        "username": "desta_eth",
        "profile": {"bio": "Just a casual chess lover"}
    }
    mock_resp = httpx.Response(status_code=200, json=mock_payload, request=httpx.Request("GET", "https://lichess.org/api/user/desta_eth"))
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        res = await adapter.verify_owner("desta_eth", "GB-4F7K")
        assert res.is_verified is False
        assert "not found" in res.error_message

@pytest.mark.asyncio
async def test_chess_com_stats_mock():
    adapter = ChessComAdapter()
    mock_payload = {
        "chess_rapid": {
            "last": {"rating": 1580, "date": 1600000000},
            "record": {"win": 45, "loss": 20, "draw": 5}
        }
    }
    mock_resp = httpx.Response(status_code=200, json=mock_payload, request=httpx.Request("GET", "https://api.chess.com/pub/player/biruk_gm/stats"))
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        res = await adapter.fetch_rating("biruk_gm", "rapid")
        assert res is not None
        assert res.rating == 1580.0
        assert res.games_played == 70
        assert res.provisional is False
