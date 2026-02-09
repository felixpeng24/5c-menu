import datetime as _dt

from sqlmodel import Field, SQLModel


class ParserRun(SQLModel, table=True):
    """Records each parser execution for health monitoring."""

    __tablename__ = "parser_runs"

    id: int | None = Field(default=None, primary_key=True)
    hall_id: str = Field(foreign_key="dining_halls.id", index=True)
    started_at: _dt.datetime = Field(
        default_factory=lambda: _dt.datetime.now(_dt.timezone.utc)
    )
    duration_ms: int | None = None
    status: str = Field(max_length=20)  # "success", "error", "fallback", "no_data"
    error_message: str | None = Field(default=None, max_length=500)
    menu_date: _dt.date | None = None
