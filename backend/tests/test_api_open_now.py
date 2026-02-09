"""Integration tests for the /api/v2/open-now endpoint."""

import datetime as _dt
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest

from app.models.dining_hours import DiningHoursOverride


# A known Monday at 12:00 Pacific -- both hoch and collins should be open for lunch
_MONDAY_NOON = _dt.datetime(2026, 2, 9, 12, 0, tzinfo=ZoneInfo("America/Los_Angeles"))
# Monday at 03:00 AM Pacific -- no halls should be open
_MONDAY_3AM = _dt.datetime(2026, 2, 9, 3, 0, tzinfo=ZoneInfo("America/Los_Angeles"))


@pytest.mark.asyncio
async def test_open_now_returns_open_halls(client, seed_hours):
    """At Monday noon, halls with lunch hours should be returned."""
    with patch("app.services.hours_service._dt.datetime") as mock_dt:
        mock_dt.now.return_value = _MONDAY_NOON
        mock_dt.side_effect = lambda *a, **kw: _dt.datetime(*a, **kw)

        resp = await client.get("/api/v2/open-now/")

    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    hall_ids = {h["id"] for h in data}
    # Both hoch (11:00-13:30) and collins (11:30-13:30) should be open
    assert "hoch" in hall_ids
    assert "collins" in hall_ids

    for h in data:
        assert h["current_meal"] == "lunch"


@pytest.mark.asyncio
async def test_open_now_returns_empty_when_closed(client, seed_hours):
    """At 3 AM, no halls should be open."""
    with patch("app.services.hours_service._dt.datetime") as mock_dt:
        mock_dt.now.return_value = _MONDAY_3AM
        mock_dt.side_effect = lambda *a, **kw: _dt.datetime(*a, **kw)

        resp = await client.get("/api/v2/open-now/")

    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_open_now_override_closes_hall(client, seed_hours, test_session):
    """An override with start_time=None closes a hall that would normally be open."""
    override = DiningHoursOverride(
        hall_id="hoch",
        date=_MONDAY_NOON.date(),
        meal="lunch",
        start_time=None,
        end_time=None,
        reason="Closed for maintenance",
    )
    test_session.add(override)
    await test_session.commit()

    with patch("app.services.hours_service._dt.datetime") as mock_dt:
        mock_dt.now.return_value = _MONDAY_NOON
        mock_dt.side_effect = lambda *a, **kw: _dt.datetime(*a, **kw)

        resp = await client.get("/api/v2/open-now/")

    assert resp.status_code == 200
    data = resp.json()
    hall_ids = {h["id"] for h in data}
    # hoch should be closed due to override
    assert "hoch" not in hall_ids
    # collins should still be open
    assert "collins" in hall_ids


@pytest.mark.asyncio
async def test_open_now_response_shape(client, seed_hours):
    """Each response item has the expected fields."""
    with patch("app.services.hours_service._dt.datetime") as mock_dt:
        mock_dt.now.return_value = _MONDAY_NOON
        mock_dt.side_effect = lambda *a, **kw: _dt.datetime(*a, **kw)

        resp = await client.get("/api/v2/open-now/")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0

    for item in data:
        assert "id" in item
        assert "name" in item
        assert "college" in item
        assert "color" in item
        assert "current_meal" in item

        assert isinstance(item["id"], str)
        assert isinstance(item["name"], str)
        assert isinstance(item["college"], str)
        assert item["color"] is None or isinstance(item["color"], str)
        assert isinstance(item["current_meal"], str)
