"""Menus router: serves menu data for a specific hall, date, and meal.

Validates inputs, delegates to the menu service for cache-aside fetching,
and returns structured MenuResponse data.
"""

import datetime as _dt

from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_redis, get_session
from app.schemas.menus import MenuResponse
from app.services.menu_service import HALL_CONFIG, get_menu

router = APIRouter(tags=["menus"])


@router.get("/", response_model=MenuResponse)
async def read_menu(
    hall_id: str,
    date: str,
    meal: str,
    session: AsyncSession = Depends(get_session),
    redis_client: Redis = Depends(get_redis),
):
    """Fetch menu data for a specific dining hall, date, and meal.

    Query parameters:
        hall_id: Dining hall identifier (e.g., "hoch", "collins").
        date: Date in YYYY-MM-DD format.
        meal: Meal period (e.g., "lunch", "dinner").

    Returns:
        MenuResponse with stations and items.

    Raises:
        404: Unknown hall_id or no menu data found.
        400: Invalid date format.
    """
    # Validate hall_id
    if hall_id not in HALL_CONFIG:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown hall_id: {hall_id}",
        )

    # Validate date format
    try:
        _dt.date.fromisoformat(date)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format, use YYYY-MM-DD",
        )

    result = await get_menu(hall_id, date, meal, session, redis_client)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No menu found for {hall_id} on {date} for {meal}",
        )

    return result
