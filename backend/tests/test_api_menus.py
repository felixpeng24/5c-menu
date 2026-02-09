"""Integration tests for the /api/v2/menus endpoint."""

import datetime as _dt
from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_get_menu_from_db(client, seed_menu):
    """GET /api/v2/menus with valid params returns menu from DB fallback."""
    today = _dt.date.today().isoformat()

    with patch(
        "app.services.menu_service.get_parser"
    ) as mock_get_parser:
        mock_parser = AsyncMock()
        mock_parser.fetch_and_parse = AsyncMock(return_value=None)
        mock_get_parser.return_value = mock_parser

        resp = await client.get(
            "/api/v2/menus/",
            params={"hall_id": "hoch", "date": today, "meal": "lunch"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["hall_id"] == "hoch"
    assert data["date"] == today
    assert data["meal"] == "lunch"
    assert "stations" in data
    assert "is_stale" in data
    assert "fetched_at" in data


@pytest.mark.asyncio
async def test_get_menu_invalid_hall(client):
    """GET /api/v2/menus with unknown hall_id returns 404."""
    resp = await client.get(
        "/api/v2/menus/",
        params={"hall_id": "nonexistent", "date": "2026-02-08", "meal": "lunch"},
    )
    assert resp.status_code == 404
    assert "Unknown hall_id" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_get_menu_invalid_date(client):
    """GET /api/v2/menus with malformed date returns 400."""
    resp = await client.get(
        "/api/v2/menus/",
        params={"hall_id": "hoch", "date": "bad-date", "meal": "lunch"},
    )
    assert resp.status_code == 400
    assert "Invalid date format" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_get_menu_not_found(client, seed_halls):
    """GET /api/v2/menus for a date with no data returns 404."""
    with patch(
        "app.services.menu_service.get_parser"
    ) as mock_get_parser:
        mock_parser = AsyncMock()
        mock_parser.fetch_and_parse = AsyncMock(return_value=None)
        mock_get_parser.return_value = mock_parser

        resp = await client.get(
            "/api/v2/menus/",
            params={"hall_id": "hoch", "date": "2026-01-01", "meal": "lunch"},
        )

    assert resp.status_code == 404
    assert "No menu found" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_menu_cached_on_second_request(client, seed_menu, fake_redis):
    """First request populates cache; second request finds cache hit."""
    today = _dt.date.today().isoformat()

    with patch(
        "app.services.menu_service.get_parser"
    ) as mock_get_parser:
        mock_parser = AsyncMock()
        mock_parser.fetch_and_parse = AsyncMock(return_value=None)
        mock_get_parser.return_value = mock_parser

        # First request: cache miss -> falls through to DB
        resp1 = await client.get(
            "/api/v2/menus/",
            params={"hall_id": "hoch", "date": today, "meal": "lunch"},
        )
        assert resp1.status_code == 200

        # Check that the cache key now exists
        cache_key = f"menu:hoch:{today}:lunch"
        cached_value = await fake_redis.get(cache_key)
        assert cached_value is not None

        # Second request: should hit cache (parser not invoked again)
        mock_get_parser.reset_mock()
        resp2 = await client.get(
            "/api/v2/menus/",
            params={"hall_id": "hoch", "date": today, "meal": "lunch"},
        )
        assert resp2.status_code == 200
        assert resp2.json() == resp1.json()


@pytest.mark.asyncio
async def test_menu_response_shape(client, seed_menu):
    """Response matches MenuResponse schema structure."""
    today = _dt.date.today().isoformat()

    with patch(
        "app.services.menu_service.get_parser"
    ) as mock_get_parser:
        mock_parser = AsyncMock()
        mock_parser.fetch_and_parse = AsyncMock(return_value=None)
        mock_get_parser.return_value = mock_parser

        resp = await client.get(
            "/api/v2/menus/",
            params={"hall_id": "hoch", "date": today, "meal": "lunch"},
        )

    assert resp.status_code == 200
    data = resp.json()

    # Top-level fields
    assert isinstance(data["stations"], list)
    assert isinstance(data["is_stale"], bool)
    assert data["fetched_at"] is None or isinstance(data["fetched_at"], str)

    # Station structure
    for station in data["stations"]:
        assert "name" in station
        assert "items" in station
        assert isinstance(station["name"], str)
        assert isinstance(station["items"], list)

        # Item structure
        for item in station["items"]:
            assert "name" in item
            assert "tags" in item
            assert isinstance(item["name"], str)
            assert isinstance(item["tags"], list)
