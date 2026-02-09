from pydantic import BaseModel


class HallResponse(BaseModel):
    """Response schema for a dining hall."""

    id: str
    name: str
    college: str
    vendor_type: str
    color: str | None = None
