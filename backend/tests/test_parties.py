"""POST /parties: login requirement and input validation. No DB access needed."""

import uuid
from collections.abc import Iterator
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.auth import get_current_user
from app.main import app
from app.models import User
from app.models.base import utcnow

VALID_BODY = {"name": "Bday", "party_at": "2099-01-01T19:00:00+05:30"}


def iso(delta: timedelta) -> str:
    return (utcnow() + delta).isoformat()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def logged_in() -> Iterator[None]:
    """Pretend a host is signed in by replacing the get_current_user dependency."""
    fake = User(id=uuid.uuid4(), google_sub="test-sub", email="host@example.com")
    app.dependency_overrides[get_current_user] = lambda: fake
    yield
    app.dependency_overrides.clear()


def test_create_party_requires_login(client: TestClient) -> None:
    assert client.post("/parties", json=VALID_BODY).status_code == 401


@pytest.mark.usefixtures("logged_in")
@pytest.mark.parametrize(
    "body",
    [
        pytest.param({"name": "   ", "party_at": iso(timedelta(days=2))}, id="blank-name"),
        pytest.param({"name": "Bday", "party_at": iso(timedelta(days=-1))}, id="party-in-past"),
        pytest.param({"name": "Bday", "party_at": "2099-01-01T19:00:00"}, id="no-timezone"),
        pytest.param(
            {
                "name": "Bday",
                "party_at": iso(timedelta(days=2)),
                "rsvp_deadline": iso(timedelta(days=3)),
            },
            id="deadline-after-party",
        ),
        pytest.param(
            {"name": "Bday", "party_at": iso(timedelta(days=2)), "budget_per_person_paise": -1},
            id="negative-budget",
        ),
    ],
)
def test_create_party_rejects_bad_input(client: TestClient, body: dict) -> None:
    assert client.post("/parties", json=body).status_code == 422
