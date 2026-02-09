from pydantic import BaseModel


class OpenHallResponse(BaseModel):
    """Response schema for a dining hall that is currently open."""

    id: str
    name: str
    college: str
    color: str | None = None
    current_meal: str
