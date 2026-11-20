"""Sign-in endpoints: POST /auth/google, GET /auth/me, POST /auth/logout."""

from fastapi import APIRouter, Response, status

from app.auth import (
    SESSION_COOKIE,
    CurrentUser,
    create_session_token,
    get_or_create_user,
    verify_google_id_token,
)
from app.config import get_settings
from app.db import SessionDep
from app.log import get_logger
from app.models import User
from app.schemas.auth import GoogleLogin, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])
log = get_logger(__name__)


def _user_out(user: User) -> UserOut:
    return UserOut(id=user.id, email=user.email, name=user.name)


@router.post("/google")
async def login_with_google(body: GoogleLogin, response: Response, session: SessionDep) -> UserOut:
    identity = await verify_google_id_token(body.credential)
    user = await get_or_create_user(session, identity)

    settings = get_settings()
    response.set_cookie(
        key=SESSION_COOKIE,
        value=create_session_token(user.id),
        max_age=settings.session_days * 24 * 60 * 60,
        httponly=True,  # JavaScript can't read it, so an XSS bug can't steal the session
        secure=settings.app_env != "local",  # HTTPS-only outside localhost
        samesite="lax",  # not sent on cross-site POSTs, which blocks CSRF
    )
    log.info("host signed in")  # no email/name: PII stays out of logs
    return _user_out(user)


@router.get("/me")
async def me(user: CurrentUser) -> UserOut:
    return _user_out(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE)
