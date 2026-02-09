from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.dependencies import get_session
from app.models.dining_hall import DiningHall
from app.schemas.halls import HallResponse

router = APIRouter(tags=["halls"])


@router.get("/", response_model=list[HallResponse])
async def list_halls(session: AsyncSession = Depends(get_session)) -> list[HallResponse]:
    """Return all dining halls ordered by name."""
    result = await session.execute(select(DiningHall).order_by(DiningHall.name))
    halls = result.scalars().all()
    return [
        HallResponse(
            id=h.id,
            name=h.name,
            college=h.college,
            vendor_type=h.vendor_type,
            color=h.color,
        )
        for h in halls
    ]
