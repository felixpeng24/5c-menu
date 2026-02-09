import logging
from datetime import datetime, timedelta, timezone

import jwt
import resend
from fastapi import Cookie, HTTPException

from app.config import get_settings

logger = logging.getLogger(__name__)


def create_magic_link_token(email: str) -> str:
    """Create a short-lived JWT for magic link authentication."""
    settings = get_settings()
    payload = {
        "sub": email,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        "purpose": "magic_link",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def verify_magic_link_token(token: str) -> str:
    """Decode and verify a magic link JWT. Returns email on success."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        if payload.get("purpose") != "magic_link":
            raise ValueError("Invalid token purpose")
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError as exc:
        raise ValueError(f"Invalid token: {exc}")


def create_session_token(email: str) -> str:
    """Create a long-lived JWT for admin session."""
    settings = get_settings()
    payload = {
        "sub": email,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "purpose": "session",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def send_magic_link_email(email: str, token: str) -> None:
    """Send a magic link email via Resend. Fails silently on error."""
    settings = get_settings()
    resend.api_key = settings.resend_api_key
    magic_link_url = f"{settings.frontend_url}/admin/verify?token={token}"
    try:
        resend.Emails.send(
            {
                "from": f"5C Menu Admin <{settings.admin_from_email}>",
                "to": [email],
                "subject": "Your 5C Menu Admin Login Link",
                "html": (
                    f"<p>Click the link below to log in to the 5C Menu admin panel:</p>"
                    f'<p><a href="{magic_link_url}">Log in to Admin Panel</a></p>'
                    f"<p>This link expires in 15 minutes.</p>"
                ),
            }
        )
    except Exception:
        logger.exception("Failed to send magic link email to %s", email)


def require_admin(
    session_token: str | None = Cookie(default=None, alias="admin_session"),
) -> str:
    """FastAPI dependency: require a valid admin session cookie."""
    if session_token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    settings = get_settings()
    try:
        payload = jwt.decode(
            session_token, settings.jwt_secret, algorithms=["HS256"]
        )
        if payload.get("purpose") != "session":
            raise HTTPException(status_code=401, detail="Invalid session")
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid session")
