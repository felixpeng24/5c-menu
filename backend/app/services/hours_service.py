import datetime as _dt
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.dining_hall import DiningHall
from app.models.dining_hours import DiningHours, DiningHoursOverride


async def get_open_halls(
    session: AsyncSession,
    tz_name: str,
    *,
    now_override: _dt.datetime | None = None,
) -> list[dict]:
    """Return currently-open dining halls with their active meal period.

    Evaluates the current time (in *tz_name* timezone) against the
    ``DiningHours`` schedule.  Date-specific ``DiningHoursOverride``
    records take precedence:

    * Override with ``start_time=None`` -> hall is **closed** for that meal.
    * Override with times -> use those times instead of the regular schedule.
    * Override for a meal with no regular-hours row -> special opening.

    If a hall qualifies for multiple meals simultaneously, only the meal
    whose ``start_time`` is most recent is returned.

    Parameters
    ----------
    session:
        Async database session.
    tz_name:
        IANA timezone name (e.g. ``"America/Los_Angeles"``).
    now_override:
        Optional fixed datetime for deterministic testing.  When provided,
        ``_dt.datetime.now()`` is **not** called.
    """
    tz = ZoneInfo(tz_name)
    now = now_override if now_override is not None else _dt.datetime.now(tz)
    if now.tzinfo is None:
        now = now.replace(tzinfo=tz)

    current_time = now.time()
    # isoweekday(): Monday=1 .. Sunday=7  ->  Sunday=0 .. Saturday=6
    current_dow = now.isoweekday() % 7

    # -- 1. Fetch today's overrides -----------------------------------------
    override_result = await session.execute(
        select(DiningHoursOverride).where(
            DiningHoursOverride.date == now.date()
        )
    )
    overrides = override_result.scalars().all()
    override_map: dict[tuple[str, str | None], DiningHoursOverride] = {
        (o.hall_id, o.meal): o for o in overrides
    }

    # -- 2. Fetch regular hours for today's day-of-week ---------------------
    hours_result = await session.execute(
        select(DiningHours).where(
            DiningHours.day_of_week == current_dow,
            DiningHours.is_active == True,  # noqa: E712
        )
    )
    regular_hours = hours_result.scalars().all()

    # Collect (hall_id, meal, effective_start) for halls currently open
    open_entries: dict[str, tuple[str, _dt.time]] = {}  # hall_id -> (meal, start)

    seen_keys: set[tuple[str, str | None]] = set()

    for row in regular_hours:
        key = (row.hall_id, row.meal)
        seen_keys.add(key)

        override = override_map.get(key)
        if override is not None:
            if override.start_time is None:
                # Explicitly closed for this meal
                continue
            start = override.start_time
            end = override.end_time
        else:
            start = row.start_time
            end = row.end_time

        if start is not None and end is not None and start <= current_time <= end:
            existing = open_entries.get(row.hall_id)
            if existing is None or start > existing[1]:
                open_entries[row.hall_id] = (row.meal, start)

    # -- 3. Check override-only entries (special openings) ------------------
    for (hall_id, meal), override in override_map.items():
        if (hall_id, meal) in seen_keys:
            continue  # Already handled above
        if override.start_time is None or override.end_time is None:
            continue  # Closure-only override without regular hours (no-op)
        if override.start_time <= current_time <= override.end_time:
            existing = open_entries.get(hall_id)
            if existing is None or override.start_time > existing[1]:
                open_entries[hall_id] = (meal or "special", override.start_time)

    if not open_entries:
        return []

    # -- 4. Fetch hall metadata for open halls ------------------------------
    hall_ids = list(open_entries.keys())
    hall_result = await session.execute(
        select(DiningHall).where(DiningHall.id.in_(hall_ids))  # type: ignore[attr-defined]
    )
    halls = {h.id: h for h in hall_result.scalars().all()}

    results: list[dict] = []
    for hall_id, (meal, _start) in open_entries.items():
        hall = halls.get(hall_id)
        if hall is None:
            continue
        results.append(
            {
                "id": hall.id,
                "name": hall.name,
                "college": hall.college,
                "color": hall.color,
                "current_meal": meal,
            }
        )

    return results
