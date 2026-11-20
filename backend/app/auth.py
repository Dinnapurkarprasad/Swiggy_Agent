"""Host sign-in: verify Google's ID token, issue our own login cookie, read it back.

Flow:
    frontend Google button -> Google ID token -> POST /auth/google
    -> verify_google_id_token() -> get_or_create_user() -> set cookie (create_session_token)
    later requests -> get_current_user() reads the cookie -> CurrentUser
"""

import asyncio
import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Annotated

import jwt
from fastapi import Cookie, Depends, HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlmodel import select

from app.config import get_settings
from app.db import SessionDep
from app.models import User
from app.models.base import utcnow

SESSION_COOKIE = "party_session"
_JWT_ALGORITHM = "HS256"


def _unauthorized(detail: str = "Not logged in") -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def _session_secret() -> str:
    secret = get_settings().session_secret
    if secret is None:
        raise RuntimeError("SESSION_SECRET is not set")
    return secret.get_secret_value()


# --- Google ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GoogleIdentity:
    sub: str
    email: str
    name: str | None


def _verify_sync(credential: str, client_id: str) -> GoogleIdentity:
    # Checks the signature against Google's public keys, the expiry, the issuer
    # (accounts.google.com) and that the token was issued for OUR client id.
    claims = id_token.verify_oauth2_token(
        credential, google_requests.Request(), client_id, clock_skew_in_seconds=10
    )
    if not claims.get("email_verified"):
        raise ValueError("Google email is not verified")
    return GoogleIdentity(sub=claims["sub"], email=claims["email"], name=claims.get("name"))


async def verify_google_id_token(credential: str) -> GoogleIdentity:
    client_id = get_settings().google_oauth_client_id
    if not client_id:
        raise RuntimeError("GOOGLE_OAUTH_CLIENT_ID is not set")
    try:
        # google-auth is synchronous (it may fetch Google's keys over HTTP), so run it
        # in a worker thread instead of blocking the event loop.
        return await asyncio.to_thread(_verify_sync, credential, client_id)
    except ValueError as exc:  # bad signature, expired, wrong audience, unverified email
        raise _unauthorized("Invalid Google sign-in") from exc


async def get_or_create_user(session: SessionDep, identity: GoogleIdentity) -> User:
    """Sign-up and log-in are the same: first sign-in creates the user."""
    user = (await session.exec(select(User).where(User.google_sub == identity.sub))).one_or_none()
    if user is None:
        user = User(google_sub=identity.sub, email=identity.email, name=identity.name)
        session.add(user)
    else:  # keep email/name current if they changed on Google's side
        user.email = identity.email
        user.name = identity.name
    await session.commit()
    return user


# --- Our login cookie -----------------------------------------------------------------


def create_session_token(user_id: uuid.UUID) -> str:
    now = utcnow()
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(days=get_settings().session_days),
    }
    return jwt.encode(payload, _session_secret(), algorithm=_JWT_ALGORITHM)


def read_session_token(token: str) -> uuid.UUID:
    """Return the user id inside a valid cookie; raise 401 if forged, expired or malformed."""
    try:
        payload = jwt.decode(token, _session_secret(), algorithms=[_JWT_ALGORITHM])
        return uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise _unauthorized("Session expired, please sign in again") from exc


async def get_current_user(
    session: SessionDep,
    party_session: Annotated[str | None, Cookie()] = None,
) -> User:
    if not party_session:
        raise _unauthorized()
    user = await session.get(User, read_session_token(party_session))
    if user is None:  # account was deleted after the cookie was issued
        raise _unauthorized()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
