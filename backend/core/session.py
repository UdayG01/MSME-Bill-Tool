"""Opaque, short-lived sessions for the current single-worker deployment.

Business records are stored in PostgreSQL; only login state is process-local.
Consequently, a backend restart can log a user out without losing any invoices,
customers, receipts, credit notes, or company data. Use a database or Redis
session store before scaling the backend beyond one worker.
"""
import secrets
import time
from typing import Optional

from fastapi import HTTPException, Request, status

from core.config import get_settings

SESSION_COOKIE_NAME = "msme_session"
SESSION_TTL_SECONDS = get_settings().session_ttl_seconds

# token -> {"user_id": str, "tenant_id": str, "created_at": float}
_SESSIONS: dict[str, dict] = {}


def create_session(user_id: str, tenant_id: str) -> str:
    token = secrets.token_urlsafe(32)
    _SESSIONS[token] = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "created_at": time.time(),
    }
    return token


def destroy_session(token: str) -> None:
    _SESSIONS.pop(token, None)


def _get_session(token: Optional[str]) -> Optional[dict]:
    if not token:
        return None
    session = _SESSIONS.get(token)
    if not session:
        return None
    if time.time() - session["created_at"] > SESSION_TTL_SECONDS:
        _SESSIONS.pop(token, None)
        return None
    return session


def get_current_session(request: Request) -> dict:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    session = _get_session(token)
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return session
