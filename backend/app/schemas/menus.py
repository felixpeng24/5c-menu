from pydantic import BaseModel


class MenuItemResponse(BaseModel):
    """Response schema for a single menu item."""

    name: str
    tags: list[str] = []


class StationResponse(BaseModel):
    """Response schema for a station within a meal."""

    name: str
    items: list[MenuItemResponse]


class MenuResponse(BaseModel):
    """Response schema for a complete menu (hall + date + meal)."""

    hall_id: str
    date: str
    meal: str
    stations: list[StationResponse]
    is_stale: bool = False
    fetched_at: str | None = None
