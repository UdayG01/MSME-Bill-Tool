from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from db import schemas, get_db
from core.config import get_settings
from core.session import create_session, destroy_session, get_current_session, SESSION_COOKIE_NAME
from services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        max_age=settings.session_ttl_seconds,
        path="/",
    )


@router.post("/signup", status_code=201)
def signup(payload: schemas.SignupIn, response: Response, db: Session = Depends(get_db)):
    user, tenant = auth_service.signup(db, payload)
    token = create_session(user.id, tenant.id)
    _set_session_cookie(response, token)
    return {"tenant_id": tenant.id, "user_id": user.id}


@router.post("/login")
def login(payload: schemas.LoginIn, response: Response, db: Session = Depends(get_db)):
    user = auth_service.login(db, payload)
    token = create_session(user.id, user.tenant_id)
    _set_session_cookie(response, token)
    return {"tenant_id": user.tenant_id, "user_id": user.id}


@router.post("/logout")
def logout(request: Request, response: Response, session=Depends(get_current_session)):
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        destroy_session(token)
    response.delete_cookie(SESSION_COOKIE_NAME, path="/", secure=settings.session_cookie_secure, samesite=settings.session_cookie_samesite)
    return {"ok": True}


@router.get("/me")
def me(session=Depends(get_current_session), db: Session = Depends(get_db)):
    return auth_service.current_identity(db, session["user_id"], session["tenant_id"])
