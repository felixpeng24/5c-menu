import datetime as _dt

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class DiningHours(SQLModel, table=True):
    """Regular weekly operating hours for a dining hall meal period."""

    __tablename__ = "dining_hours"
    __table_args__ = (
        UniqueConstraint("hall_id", "day_of_week", "meal", name="uq_hours_hall_day_meal"),
    )

    id: int | None = Field(default=None, primary_key=True)
    hall_id: str = Field(foreign_key="dining_halls.id", index=True)
    day_of_week: int = Field(ge=0, le=6)  # 0=Sunday .. 6=Saturday
    meal: str = Field(max_length=20)
    start_time: _dt.time
    end_time: _dt.time
    is_active: bool = Field(default=True)


class DiningHoursOverride(SQLModel, table=True):
    """Date-specific overrides for dining hall hours (closures, special hours)."""

    __tablename__ = "dining_hours_overrides"
    __table_args__ = (
        UniqueConstraint("hall_id", "date", "meal", name="uq_override_hall_date_meal"),
    )

    id: int | None = Field(default=None, primary_key=True)
    hall_id: str = Field(foreign_key="dining_halls.id", index=True)
    date: _dt.date
    meal: str | None = Field(default=None, max_length=20)
    start_time: _dt.time | None = None
    end_time: _dt.time | None = None
    reason: str | None = Field(default=None, max_length=200)
