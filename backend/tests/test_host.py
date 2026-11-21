"""Host routes require sign-in."""

import uuid

from fastapi.testclient import TestClient

from app.main import app


def test_host_routes_require_login() -> None:
    client = TestClient(app)
    assert client.get("/host/parties").status_code == 401
    assert client.get(f"/host/parties/{uuid.uuid4()}").status_code == 401
