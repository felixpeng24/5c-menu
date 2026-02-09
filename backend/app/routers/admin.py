import datetime as _dt
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.config import get_settings
from app.dependencies import get_session
from app.models.dining_hours import DiningHours, DiningHoursOverride
from app.schemas.admin import (
    HoursCreate,
    HoursResponse,
    HoursUpdate,
    MagicLinkRequest,
    MagicLinkVerify,
    OverrideCreate,
    OverrideResponse,
    OverrideUpdate,
)
from app.services.auth_service import (
    create_magic_link_token,
    create_session_token,
    require_admin,
    send_magic_link_email,
    verify_magic_link_token,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin"])


@router.post("/auth/request-link")
def request_magic_link(body: MagicLinkRequest):
    """Request a magic link email for admin login.

    Always returns the same response regardless of whether the email
    matches, to prevent email enumeration.
    """
    settings = get_settings()
    if not settings.admin_email:
        logger.warning("FIVEC_ADMIN_EMAIL not set; magic link request ignored")
    elif body.email.lower() == settings.admin_email.lower():
        token = create_magic_link_token(body.email.lower())
        send_magic_link_email(body.email.lower(), token)

    return {"message": "If this email is registered, a login link has been sent."}


@router.post("/auth/verify")
def verify_magic_link(body: MagicLinkVerify):
    """Verify a magic link token and create an admin session."""
    try:
        email = verify_magic_link_token(body.token)
    except ValueError:
        return JSONResponse(
            status_code=401, content={"detail": "Invalid or expired token"}
        )

    session_token = create_session_token(email)
    response = JSONResponse(content={"message": "Authenticated"})
    response.set_cookie(
        key="admin_session",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
    )
    return response


@router.post("/auth/logout")
def logout(admin_email: str = Depends(require_admin)):
    """Log out the admin by deleting the session cookie."""
    response = JSONResponse(content={"message": "Logged out"})
    response.delete_cookie(key="admin_session")
    return response


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _hours_to_response(h: DiningHours) -> HoursResponse:
    return HoursResponse(
        id=h.id,
        hall_id=h.hall_id,
        day_of_week=h.day_of_week,
        meal=h.meal,
        start_time=h.start_time.isoformat(),
        end_time=h.end_time.isoformat(),
        is_active=h.is_active,
    )


def _override_to_response(o: DiningHoursOverride) -> OverrideResponse:
    return OverrideResponse(
        id=o.id,
        hall_id=o.hall_id,
        date=o.date.isoformat(),
        meal=o.meal,
        start_time=o.start_time.isoformat() if o.start_time else None,
        end_time=o.end_time.isoformat() if o.end_time else None,
        reason=o.reason,
    )


# ---------------------------------------------------------------------------
# Hours CRUD
# ---------------------------------------------------------------------------


@router.get("/hours", response_model=list[HoursResponse])
async def list_hours(
    admin_email: str = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    """Return all dining hours entries, ordered by hall, day, meal."""
    stmt = select(DiningHours).order_by(
        DiningHours.hall_id, DiningHours.day_of_week, DiningHours.meal
    )
    result = await session.execute(stmt)
    rows = result.scalars().all()
    return [_hours_to_response(h) for h in rows]


@router.post("/hours", response_model=HoursResponse, status_code=201)
async def create_hours(
    body: HoursCreate,
    admin_email: str = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    """Create a new dining hours entry."""
    row = DiningHours(
        hall_id=body.hall_id,
        day_of_week=body.day_of_week,
        meal=body.meal,
        start_time=_dt.time.fromisoformat(body.start_time),
        end_time=_dt.time.fromisoformat(body.end_time),
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _hours_to_response(row)


@router.put("/hours/{hours_id}", response_model=HoursResponse)
async def update_hours(
    hours_id: int,
    body: HoursUpdate,
    admin_email: str = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    """Update an existing dining hours entry."""
    row = await session.get(DiningHours, hours_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Hours entry not found")
    if body.start_time is not None:
        row.start_time = _dt.time.fromisoformat(body.start_time)
    if body.end_time is not None:
        row.end_time = _dt.time.fromisoformat(body.end_time)
    if body.is_active is not None:
        row.is_active = body.is_active
    await session.commit()
    await session.refresh(row)
    return _hours_to_response(row)


@router.delete("/hours/{hours_id}")
async def delete_hours(
    hours_id: int,
    admin_email: str = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    """Delete a dining hours entry."""
    row = await session.get(DiningHours, hours_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Hours entry not found")
    await session.delete(row)
    await session.commit()
    return {"message": "Deleted"}


# ---------------------------------------------------------------------------
# Overrides CRUD
# ---------------------------------------------------------------------------


@router.get("/overrides", response_model=list[OverrideResponse])
async def list_overrides(
    admin_email: str = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    """Return all dining hours overrides, ordered by date descending."""
    stmt = select(DiningHoursOverride).order_by(DiningHoursOverride.date.desc())
    result = await session.execute(stmt)
    rows = result.scalars().all()
    return [_override_to_response(o) for o in rows]


@router.post("/overrides", response_model=OverrideResponse, status_code=201)
async def create_override(
    body: OverrideCreate,
    admin_email: str = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    """Create a new dining hours override."""
    row = DiningHoursOverride(
        hall_id=body.hall_id,
        date=_dt.date.fromisoformat(body.date),
        meal=body.meal,
        start_time=_dt.time.fromisoformat(body.start_time) if body.start_time else None,
        end_time=_dt.time.fromisoformat(body.end_time) if body.end_time else None,
        reason=body.reason,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _override_to_response(row)


@router.put("/overrides/{override_id}", response_model=OverrideResponse)
async def update_override(
    override_id: int,
    body: OverrideUpdate,
    admin_email: str = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    """Update an existing dining hours override."""
    row = await session.get(DiningHoursOverride, override_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Override not found")
    if body.start_time is not None:
        row.start_time = _dt.time.fromisoformat(body.start_time)
    if body.end_time is not None:
        row.end_time = _dt.time.fromisoformat(body.end_time)
    if body.reason is not None:
        row.reason = body.reason
    await session.commit()
    await session.refresh(row)
    return _override_to_response(row)


@router.delete("/overrides/{override_id}")
async def delete_override(
    override_id: int,
    admin_email: str = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    """Delete a dining hours override."""
    row = await session.get(DiningHoursOverride, override_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Override not found")
    await session.delete(row)
    await session.commit()
    return {"message": "Deleted"}
