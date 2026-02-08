import datetime as _dt
from typing import Any

from pydantic import BaseModel
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON
from sqlmodel import Field, SQLModel


# ---------------------------------------------------------------------------
# Pydantic models for parsed data interchange (NOT database tables)
# ---------------------------------------------------------------------------


class ParsedMenuItem(BaseModel):
    """A single menu item with optional dietary tags."""

    name: str
    tags: list[str] = []


class ParsedStation(BaseModel):
    """A station within a meal containing menu items."""

    name: str
    items: list[ParsedMenuItem]


class ParsedMeal(BaseModel):
    """A meal period (e.g., lunch) with its stations."""

    meal: str
    stations: list[ParsedStation]


class ParsedMenu(BaseModel):
    """Complete parsed menu for a single hall and date."""

    hall_id: str
    date: _dt.date
    meals: list[ParsedMeal]


# ---------------------------------------------------------------------------
# SQLModel table for persisted menu data
# ---------------------------------------------------------------------------


class Menu(SQLModel, table=True):
    """Persisted menu data for a hall/date/meal combination.

    stations_json stores the station->items hierarchy as JSONB.
    """

    __tablename__ = "menus"
    __table_args__ = (
        UniqueConstraint("hall_id", "date", "meal", name="uq_menu_hall_date_meal"),
    )

    id: int | None = Field(default=None, primary_key=True)
    hall_id: str = Field(foreign_key="dining_halls.id", index=True)
    date: _dt.date = Field(index=True)
    meal: str = Field(max_length=20)
    stations_json: Any = Field(default=None, sa_column=Column(JSON, nullable=False))
    fetched_at: _dt.datetime = Field(default_factory=_dt.datetime.utcnow)
    is_valid: bool = Field(default=True)
