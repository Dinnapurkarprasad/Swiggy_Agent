"""Request/response models for party endpoints."""

import uuid
from typing import Annotated, Self

from pydantic import AwareDatetime, BaseModel, Field, StringConstraints, model_validator

from app.models.base import utcnow
from app.models.enums import PartyStatus

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
