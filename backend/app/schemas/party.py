"""Request/response models for party endpoints."""

import uuid
from typing import Annotated, Self

from pydantic import AwareDatetime, BaseModel, Field, StringConstraints, model_validator

from app.models.base import utcnow
from app.models.enums import (
    Allergy,
    Beverage,
    Cuisine,
    FoodType,
    HungerLevel,
    PartyStatus,
    Restriction,
    SpiceLevel,
)
from app.schemas.guest import GuestResponseOut

PartyName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class PartyCreate(BaseModel):
    """What the host sends to create a party."""

    name: PartyName
    # AwareDatetime rejects times without a timezone, e.g. "2026-12-01T19:00" (ambiguous).
    party_at: AwareDatetime
    budget_per_person_paise: int | None = Field(default=None, ge=0)
    rsvp_deadline: AwareDatetime | None = None

    @model_validator(mode="after")
    def check_times(self) -> Self:
        if self.party_at <= utcnow():
            raise ValueError("party_at must be in the future")
        if self.rsvp_deadline is not None:
            if self.rsvp_deadline <= utcnow():
                raise ValueError("rsvp_deadline must be in the future")
            if self.rsvp_deadline >= self.party_at:
                raise ValueError("rsvp_deadline must be before party_at")
        return self


class PartyCreated(BaseModel):
    """Returned right after creation: the link the host shares with guests."""

    id: uuid.UUID
    name: str
    party_at: AwareDatetime
    status: PartyStatus
    guest_url: str


class PartyPublic(BaseModel):
    """What anyone with the guest link may see. No host details, no other guests."""

    id: uuid.UUID
    name: str
    party_at: AwareDatetime
    rsvp_deadline: AwareDatetime | None
    accepting_responses: bool


class PartyListItem(BaseModel):
    """One row on the host's 'my parties' page."""

    id: uuid.UUID
    name: str
    party_at: AwareDatetime
    status: PartyStatus
    response_count: int
    guest_url: str


class PartySummary(BaseModel):
    """Totals the host sees at a glance (and the agent will reuse).

    Counts are per guest response; plus-ones have no diet data of their own and only
    add to `headcount`.
    """

    responses: int
    headcount: int  # guests + their plus-ones
    with_kids: int
    food_types: dict[FoodType, int]
    restrictions: dict[Restriction, int]
    allergies: dict[Allergy, int]
    other_allergies: list[str]  # free text: can't be checked automatically, show as warnings
    spice: dict[SpiceLevel, int]
    top_cuisines: list[tuple[Cuisine, int]]
    hunger: dict[HungerLevel, int]  # unanswered counts as regular
    beverages: dict[Beverage, int]
    want_dessert: int


class PartyDetail(BaseModel):
    """Host dashboard for one party."""

    id: uuid.UUID
    name: str
    party_at: AwareDatetime
    rsvp_deadline: AwareDatetime | None
    budget_per_person_paise: int | None
    status: PartyStatus
    guest_url: str
    summary: PartySummary
    responses: list[GuestResponseOut]
