from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.dependencies import get_session
from app.schemas.open_now import OpenHallResponse
from app.services.hours_service import get_open_halls

router = APIRouter(tags=["open-now"])


@router.get("/", response_model=list[OpenHallResponse])
async def list_open_halls(
    session: AsyncSession = Depends(get_session),
) -> list[OpenHallResponse]:
    """Return dining halls that are currently open with their active meal."""
    settings = get_settings()
    open_halls = await get_open_halls(session, settings.timezone)
    return [OpenHallResponse(**h) for h in open_halls]
