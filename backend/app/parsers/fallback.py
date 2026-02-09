"""Fallback orchestrator for parser failure resilience.

When a parser fails to fetch or parse live data, the orchestrator falls back
to the last-known-good menu data stored in PostgreSQL. Fresh data is persisted
on every successful parse for future fallback use.
"""

import datetime as _dt
import logging
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.parser_run import ParserRun
from app.models.menu import (
    Menu,
    ParsedMeal,
    ParsedMenu,
    ParsedMenuItem,
    ParsedStation,
)
from app.parsers.base import BaseParser

logger = logging.getLogger(__name__)


async def persist_menu(
    session: AsyncSession,
    hall_id: str,
    target_date: _dt.date,
    menu: ParsedMenu,
) -> None:
    """Persist a parsed menu to the database for fallback use.

    Upserts one row per meal period (hall_id + date + meal). Serializes
    the station hierarchy as JSON in the ``stations_json`` column.
    """
    for meal in menu.meals:
        stations_data = [
            {
                "name": station.name,
                "items": [
                    {"name": item.name, "tags": item.tags}
                    for item in station.items
                ],
            }
            for station in meal.stations
        ]

        # Check for existing row
        stmt = select(Menu).where(
            Menu.hall_id == hall_id,
            Menu.date == target_date,
            Menu.meal == meal.meal,
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is not None:
            existing.stations_json = stations_data
            existing.fetched_at = _dt.datetime.now(_dt.timezone.utc)
            existing.is_valid = True
        else:
            new_menu = Menu(
                hall_id=hall_id,
                date=target_date,
                meal=meal.meal,
                stations_json=stations_data,
                fetched_at=_dt.datetime.now(_dt.timezone.utc),
                is_valid=True,
            )
            session.add(new_menu)

    await session.commit()


async def load_latest_menu(
    session: AsyncSession,
    hall_id: str,
    target_date: _dt.date,
) -> tuple[ParsedMenu | None, _dt.datetime | None]:
    """Load the most recent valid menu from the database.

    Returns ``(menu, fetched_at)`` or ``(None, None)`` if no stored data.
    """
    stmt = (
        select(Menu)
        .where(
            Menu.hall_id == hall_id,
            Menu.date == target_date,
            Menu.is_valid == True,  # noqa: E712
        )
        .order_by(Menu.fetched_at.desc())
    )
    result = await session.execute(stmt)
    rows = result.scalars().all()

    if not rows:
        return None, None

    # Group by meal period (take the most recent for each)
    seen_meals: set[str] = set()
    meals: list[ParsedMeal] = []
    latest_fetched_at: _dt.datetime | None = None

    for row in rows:
        if row.meal in seen_meals:
            continue
        seen_meals.add(row.meal)

        if latest_fetched_at is None or row.fetched_at > latest_fetched_at:
            latest_fetched_at = row.fetched_at

        # Reconstruct ParsedMeal from stored JSON
        stations: list[ParsedStation] = []
        for station_data in (row.stations_json or []):
            items = [
                ParsedMenuItem(
                    name=item["name"],
                    tags=item.get("tags", []),
                )
                for item in station_data.get("items", [])
            ]
            stations.append(ParsedStation(name=station_data["name"], items=items))

        meals.append(ParsedMeal(meal=row.meal, stations=stations))

    if not meals:
        return None, None

    menu = ParsedMenu(hall_id=hall_id, date=target_date, meals=meals)
    return menu, latest_fetched_at


async def _record_run(
    session: AsyncSession,
    hall_id: str,
    target_date: _dt.date,
    start: float,
    status: str,
    error_message: str | None = None,
) -> None:
    """Best-effort recording of a parser run for health tracking."""
    try:
        duration_ms = int((time.monotonic() - start) * 1000)
        run = ParserRun(
            hall_id=hall_id,
            duration_ms=duration_ms,
            status=status,
            error_message=error_message,
            menu_date=target_date,
        )
        session.add(run)
        await session.commit()
    except Exception:
        logger.warning(
            "Failed to record parser run for %s", hall_id, exc_info=True
        )


async def get_menu_with_fallback(
    parser: BaseParser,
    hall_id: str,
    target_date: _dt.date,
    session: AsyncSession,
) -> tuple[ParsedMenu | None, bool, _dt.datetime | None]:
    """Fetch a menu with fallback to last-known-good data.

    Returns ``(menu, is_stale, fetched_at)`` where:
    - ``is_stale=False`` means fresh data from the live parser
    - ``is_stale=True`` means fallback data from the database (or None)
    """
    start = time.monotonic()
    status = "success"
    error_msg: str | None = None

    try:
        menu = await parser.fetch_and_parse(target_date)
        if menu is not None:
            now = _dt.datetime.now(_dt.timezone.utc)
            await persist_menu(session, hall_id, target_date, menu)
            await _record_run(session, hall_id, target_date, start, "success")
            return menu, False, now
        status = "no_data"
    except Exception as exc:
        logger.warning(
            "Parser failed for %s on %s",
            hall_id,
            target_date,
            exc_info=True,
        )
        status = "error"
        error_msg = str(exc)[:500]

    await _record_run(session, hall_id, target_date, start, status, error_msg)

    # Fallback: load last-known-good from database
    stored_menu, stored_fetched_at = await load_latest_menu(
        session, hall_id, target_date
    )
    if stored_menu is not None:
        return stored_menu, True, stored_fetched_at

    return None, True, None
