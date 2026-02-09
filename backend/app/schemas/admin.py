from pydantic import BaseModel


class MagicLinkRequest(BaseModel):
    """Request body for requesting a magic link email."""

    email: str


class MagicLinkVerify(BaseModel):
    """Request body for verifying a magic link token."""

    token: str


class HoursResponse(BaseModel):
    """Response schema for dining hours."""

    id: int
    hall_id: str
    day_of_week: int
    meal: str
    start_time: str
    end_time: str
    is_active: bool


class HoursUpdate(BaseModel):
    """Request body for updating dining hours."""

    start_time: str | None = None
    end_time: str | None = None
    is_active: bool | None = None


class HoursCreate(BaseModel):
    """Request body for creating dining hours."""

    hall_id: str
    day_of_week: int
    meal: str
    start_time: str
    end_time: str


class OverrideResponse(BaseModel):
    """Response schema for dining hours overrides."""

    id: int
    hall_id: str
    date: str
    meal: str | None
    start_time: str | None
    end_time: str | None
    reason: str | None


class OverrideCreate(BaseModel):
    """Request body for creating a dining hours override."""

    hall_id: str
    date: str
    meal: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    reason: str | None = None


class OverrideUpdate(BaseModel):
    """Request body for updating a dining hours override."""

    start_time: str | None = None
    end_time: str | None = None
    reason: str | None = None


class ParserHealthResponse(BaseModel):
    """Response schema for parser health status."""

    hall_id: str
    last_success: str | None
    total_runs_24h: int
    error_count_24h: int
    error_rate: float
