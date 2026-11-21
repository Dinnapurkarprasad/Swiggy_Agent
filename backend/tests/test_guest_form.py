"""Guest form rules. Invalid bodies are rejected with 422 before any DB access."""

import uuid

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.schemas.guest import GuestResponseCreate

MINIMAL = {"name": "Riya", "food_type": "pure_veg", "spice": "mild"}


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_minimal_form_is_valid() -> None:
    form = GuestResponseCreate.model_validate(MINIMAL)
    assert form.plus_ones == 0
    assert form.allergies == []


def test_duplicates_removed_and_blanks_become_none() -> None:
    form = GuestResponseCreate.model_validate(
        {**MINIMAL, "allergies": ["nuts", "nuts", "dairy"], "fav_dish": "   "}
    )
    assert form.allergies == ["nuts", "dairy"]
    assert form.fav_dish is None


def test_restrictions_allowed_for_non_veg() -> None:
    form = GuestResponseCreate.model_validate(
        {**MINIMAL, "food_type": "non_veg", "restrictions": ["halal_only"]}
    )
    assert form.restrictions == ["halal_only"]


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param({"name": "  "}, id="blank-name"),
        pytest.param({"food_type": "pizza"}, id="unknown-food-type"),
        pytest.param({"restrictions": ["no_beef"]}, id="restriction-for-veg"),
        pytest.param({"cuisines": ["thai", "mexican", "chinese", "japanese"]}, id="four-cuisines"),
        pytest.param({"cuisines": ["anything", "thai"]}, id="anything-plus-other"),
        pytest.param({"plus_ones": 4}, id="too-many-plus-ones"),
        pytest.param({"allergies": ["peanut-butter"]}, id="unknown-allergy"),
    ],
)
def test_invalid_forms_rejected(changes: dict) -> None:
    with pytest.raises(ValidationError):
        GuestResponseCreate.model_validate({**MINIMAL, **changes})


def test_submit_endpoint_rejects_invalid_form(client: TestClient) -> None:
    url = f"/parties/{uuid.uuid4()}/responses"
    assert client.post(url, json={**MINIMAL, "restrictions": ["no_pork"]}).status_code == 422


def test_bad_party_id_is_422(client: TestClient) -> None:
    assert client.get("/parties/not-a-uuid").status_code == 422
