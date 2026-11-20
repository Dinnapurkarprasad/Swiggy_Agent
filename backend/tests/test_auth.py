"""Sign-in and login-cookie checks. Google and the database are never contacted."""

import uuid
from datetime import timedelta

import jwt
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

import app.auth as auth
from app.config import get_settings
from app.main import app
from app.models.base import utcnow

TEST_SECRET = "test-secret-at-least-32-bytes-long!!"


@pytest.fixture(autouse=True)
def session_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "session_secret", SecretStr(TEST_SECRET))
    monkeypatch.setattr(get_settings(), "google_oauth_client_id", "test.apps.googleusercontent.com")


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_session_token_round_trip() -> None:
    user_id = uuid.uuid4()
    assert auth.read_session_token(auth.create_session_token(user_id)) == user_id


def test_me_without_cookie_is_401(client: TestClient) -> None:
    assert client.get("/auth/me").status_code == 401


def test_me_with_forged_cookie_is_401(client: TestClient) -> None:
    forged = jwt.encode({"sub": str(uuid.uuid4())}, "attacker-secret-32-bytes-long!!!!", "HS256")
    client.cookies.set(auth.SESSION_COOKIE, forged)
    assert client.get("/auth/me").status_code == 401


def test_me_with_expired_cookie_is_401(client: TestClient) -> None:
    expired = jwt.encode(
        {"sub": str(uuid.uuid4()), "exp": utcnow() - timedelta(minutes=1)}, TEST_SECRET, "HS256"
    )
    client.cookies.set(auth.SESSION_COOKIE, expired)
    assert client.get("/auth/me").status_code == 401


def test_google_login_with_invalid_token_is_401(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def reject(credential: str, client_id: str) -> auth.GoogleIdentity:
        raise ValueError("bad signature")

    monkeypatch.setattr(auth, "_verify_sync", reject)
    response = client.post("/auth/google", json={"credential": "not-a-real-token"})
    assert response.status_code == 401
    assert auth.SESSION_COOKIE not in response.cookies


def test_logout_clears_cookie(client: TestClient) -> None:
    response = client.post("/auth/logout")
    assert response.status_code == 204
    assert f"{auth.SESSION_COOKIE}=" in response.headers["set-cookie"]
