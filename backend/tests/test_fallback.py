"""Unit tests for the fallback orchestrator.

Uses unittest.mock to mock the database session and parser behavior.
Verifies the try/except flow and persist/load logic.
"""

import datetime as _dt
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.menu import (
    Menu,
    ParsedMeal,
    ParsedMenu,
    ParsedMenuItem,
    ParsedStation,
)
from app.parsers.fallback import (
    get_menu_with_fallback,
    load_latest_menu,
    persist_menu,
)

TARGET_DATE = _dt.date(2026, 2, 7)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_menu(
    hall_id: str = "frank",
    meal_name: str = "lunch",
) -> ParsedMenu:
    """Create a simple ParsedMenu for testing."""
    return ParsedMenu(
        hall_id=hall_id,
        date=TARGET_DATE,
        meals=[
            ParsedMeal(
                meal=meal_name,
                stations=[
                    ParsedStation(
                        name="Entree",
                        items=[
                            ParsedMenuItem(name="Grilled Chicken", tags=["gluten-free"]),
                            ParsedMenuItem(name="Veggie Burger", tags=["vegan"]),
                        ],
                    ),
                    ParsedStation(
                        name="Soup",
                        items=[
                            ParsedMenuItem(name="Tomato Soup", tags=["vegetarian"]),
                        ],
                    ),
                ],
            ),
        ],
    )


def _make_db_row(
    hall_id: str = "frank",
    meal: str = "lunch",
    fetched_at: _dt.datetime | None = None,
) -> MagicMock:
    """Create a mock Menu row matching what the DB would return."""
    row = MagicMock(spec=Menu)
    row.hall_id = hall_id
    row.date = TARGET_DATE
    row.meal = meal
    row.fetched_at = fetched_at or _dt.datetime(2026, 2, 7, 12, 0, 0)
    row.is_valid = True
    row.stations_json = [
        {
            "name": "Entree",
            "items": [
                {"name": "Grilled Chicken", "tags": ["gluten-free"]},
                {"name": "Veggie Burger", "tags": ["vegan"]},
            ],
        },
        {
            "name": "Soup",
            "items": [
                {"name": "Tomato Soup", "tags": ["vegetarian"]},
            ],
        },
    ]
    return row


# ---------------------------------------------------------------------------
# persist_menu tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_persist_menu_inserts_new() -> None:
    """persist_menu inserts new rows when no existing data."""
    session = AsyncMock()
    menu = _make_menu()

    # Mock execute to return no existing row
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_result

    await persist_menu(session, "frank", TARGET_DATE, menu)

    # Should have called session.add for the meal and committed
    session.add.assert_called()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_persist_menu_updates_existing() -> None:
    """persist_menu updates existing rows when data already exists."""
    session = AsyncMock()
    menu = _make_menu()

    existing_row = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_row
    session.execute.return_value = mock_result

    await persist_menu(session, "frank", TARGET_DATE, menu)

    # Should have updated the existing row
    assert existing_row.stations_json is not None
    assert existing_row.is_valid is True
    session.commit.assert_awaited_once()
    # Should NOT have called session.add (update, not insert)
    session.add.assert_not_called()


# ---------------------------------------------------------------------------
# load_latest_menu tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_load_latest_menu_returns_data() -> None:
    """load_latest_menu reconstructs a ParsedMenu from DB rows."""
    session = AsyncMock()
    row = _make_db_row()

    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [row]
    mock_result.scalars.return_value = mock_scalars
    session.execute.return_value = mock_result

    menu, fetched_at = await load_latest_menu(session, "frank", TARGET_DATE)

    assert menu is not None
    assert isinstance(menu, ParsedMenu)
    assert menu.hall_id == "frank"
    assert len(menu.meals) == 1
    assert menu.meals[0].meal == "lunch"
    assert len(menu.meals[0].stations) == 2
    assert fetched_at is not None


@pytest.mark.asyncio
async def test_load_latest_menu_empty_db() -> None:
    """load_latest_menu returns (None, None) when no data stored."""
    session = AsyncMock()

    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    session.execute.return_value = mock_result

    menu, fetched_at = await load_latest_menu(session, "frank", TARGET_DATE)

    assert menu is None
    assert fetched_at is None


# ---------------------------------------------------------------------------
# get_menu_with_fallback tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fresh_parse_persists() -> None:
    """Successful parse returns fresh data and persists it."""
    fresh_menu = _make_menu()

    parser = MagicMock()
    parser.fetch_and_parse = AsyncMock(return_value=fresh_menu)

    session = AsyncMock()
    # Mock persist_menu's session.execute to return no existing row
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_result

    menu, is_stale, fetched_at = await get_menu_with_fallback(
        parser, "frank", TARGET_DATE, session
    )

    assert menu is not None
    assert is_stale is False
    assert fetched_at is not None
    parser.fetch_and_parse.assert_awaited_once_with(TARGET_DATE)
    # Session should have been committed (persist_menu was called)
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_fallback_on_parser_failure() -> None:
    """When parser fails, returns last-known-good data from DB."""
    parser = MagicMock()
    parser.fetch_and_parse = AsyncMock(
        side_effect=RuntimeError("Network down")
    )

    stored_row = _make_db_row(
        fetched_at=_dt.datetime(2026, 2, 7, 10, 0, 0)
    )

    session = AsyncMock()
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [stored_row]
    mock_result.scalars.return_value = mock_scalars
    session.execute.return_value = mock_result

    menu, is_stale, fetched_at = await get_menu_with_fallback(
        parser, "frank", TARGET_DATE, session
    )

    assert menu is not None
    assert is_stale is True
    assert fetched_at == _dt.datetime(2026, 2, 7, 10, 0, 0)
    assert menu.hall_id == "frank"
    assert len(menu.meals) == 1


@pytest.mark.asyncio
async def test_fallback_no_stored_data() -> None:
    """When parser fails and no stored data, returns (None, True, None)."""
    parser = MagicMock()
    parser.fetch_and_parse = AsyncMock(
        side_effect=RuntimeError("Network down")
    )

    session = AsyncMock()
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    session.execute.return_value = mock_result

    menu, is_stale, fetched_at = await get_menu_with_fallback(
        parser, "frank", TARGET_DATE, session
    )

    assert menu is None
    assert is_stale is True
    assert fetched_at is None


@pytest.mark.asyncio
async def test_fallback_when_fetch_returns_none() -> None:
    """When parser returns None (validation failure), falls back to DB."""
    parser = MagicMock()
    parser.fetch_and_parse = AsyncMock(return_value=None)

    stored_row = _make_db_row()

    session = AsyncMock()
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [stored_row]
    mock_result.scalars.return_value = mock_scalars
    session.execute.return_value = mock_result

    menu, is_stale, fetched_at = await get_menu_with_fallback(
        parser, "frank", TARGET_DATE, session
    )

    # fetch_and_parse returned None, so should fall back
    assert menu is not None
    assert is_stale is True
