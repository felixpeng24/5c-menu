"""Menu service: orchestrates cache, coalescing, parsing, and fallback.

Request flow:
1. Check Redis cache for the requested hall/date/meal
2. On cache miss, coalesce concurrent requests to prevent stampede
3. Inside the coalesced fetch: run the appropriate parser via fallback orchestrator
4. Extract the requested meal from the parsed menu
5. Cache the result and return it
"""

import datetime as _dt
import logging

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.parsers.base import BaseParser
from app.parsers.bonappetit import BonAppetitParser
from app.parsers.fallback import get_menu_with_fallback
from app.parsers.pomona import PomonaParser
from app.parsers.sodexo import SodexoParser
from app.services.cache import cache_get, cache_set, menu_cache_key
from app.services.coalesce import coalesced_fetch

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Parser registry: vendor type string -> parser class
# ---------------------------------------------------------------------------

PARSER_REGISTRY: dict[str, type[BaseParser]] = {
    "sodexo": SodexoParser,
    "bonappetit": BonAppetitParser,
    "pomona": PomonaParser,
}

# ---------------------------------------------------------------------------
# Hall configuration: hall_id -> metadata
# ---------------------------------------------------------------------------

HALL_CONFIG: dict[str, dict] = {
    "hoch": {"name": "Hoch-Shanahan", "vendor_type": "sodexo"},
    "collins": {"name": "Collins", "vendor_type": "bonappetit"},
    "malott": {"name": "Malott", "vendor_type": "bonappetit"},
    "mcconnell": {"name": "McConnell", "vendor_type": "bonappetit"},
    "frank": {"name": "Frank", "vendor_type": "pomona"},
    "frary": {"name": "Frary", "vendor_type": "pomona"},
    "oldenborg": {"name": "Oldenborg", "vendor_type": "pomona"},
}


def get_parser(hall_id: str) -> BaseParser:
    """Instantiate the correct parser for a given hall.

    Raises:
        ValueError: If hall_id is not recognized.
    """
    if hall_id not in HALL_CONFIG:
        raise ValueError(f"Unknown hall_id: {hall_id!r}")

    config = HALL_CONFIG[hall_id]
    vendor_type = config["vendor_type"]
    parser_cls = PARSER_REGISTRY[vendor_type]
    return parser_cls(hall_id=hall_id, hall_name=config["name"])


async def get_menu(
    hall_id: str,
    date_str: str,
    meal: str,
    session: AsyncSession,
    redis_client: Redis,
) -> dict | None:
    """Fetch menu data with caching and stampede prevention.

    Returns a dict matching the MenuResponse schema, or None if no
    menu data is available (neither live nor from fallback).
    """
    cache_key = menu_cache_key(hall_id, date_str, meal)

    # 1. Check cache
    cached = await cache_get(redis_client, cache_key)
    if cached is not None:
        return cached

    # 2. Cache miss -- use coalesced fetch
    async def _fetch() -> dict | None:
        target_date = _dt.date.fromisoformat(date_str)
        parser = get_parser(hall_id)

        menu, is_stale, fetched_at = await get_menu_with_fallback(
            parser, hall_id, target_date, session
        )

        if menu is None:
            return None

        # Find the matching meal period
        matching_meal = None
        for m in menu.meals:
            if m.meal.lower() == meal.lower():
                matching_meal = m
                break

        if matching_meal is None:
            return None

        # Build response dict matching MenuResponse schema
        stations = [
            {
                "name": station.name,
                "items": [
                    {"name": item.name, "tags": item.tags}
                    for item in station.items
                ],
            }
            for station in matching_meal.stations
        ]

        result: dict = {
            "hall_id": hall_id,
            "date": date_str,
            "meal": meal,
            "stations": stations,
            "is_stale": is_stale,
            "fetched_at": fetched_at.isoformat() if fetched_at else None,
        }

        # Cache the result
        await cache_set(redis_client, cache_key, result)
        return result

    return await coalesced_fetch(cache_key, _fetch)
