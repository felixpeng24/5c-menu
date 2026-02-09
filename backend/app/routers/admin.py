import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.schemas.admin import MagicLinkRequest, MagicLinkVerify
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
