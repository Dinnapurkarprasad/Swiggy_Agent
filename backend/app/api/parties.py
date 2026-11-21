"""Party endpoints: create (host) and the public guest-link routes."""

import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.common import accepting_responses, get_party_or_404, guest_url
from app.auth import CurrentUser
from app.db import SessionDep
from app.log import get_logger
from app.models import GuestResponse, Party
from app.schemas.guest import GuestResponseCreate, GuestResponseCreated
from app.schemas.party import PartyCreate, PartyCreated, PartyPublic

router = APIRouter(prefix="/parties", tags=["parties"])
log = get_logger(__name__)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_party(body: PartyCreate, host: CurrentUser, session: SessionDep) -> PartyCreated:
    party = Party(
        name=body.name,
        party_at=body.party_at,
        budget_per_person_paise=body.budget_per_person_paise,
        rsvp_deadline=body.rsvp_deadline,
        host_user_id=host.id,
    )
    session.add(party)
    await session.commit()

    log.info("party created", extra={"party_id": str(party.id)})
    return PartyCreated(
        id=party.id,
        name=party.name,
        party_at=party.party_at,
        status=party.status,
        guest_url=guest_url(party.id),
    )


@router.get("/{party_id}")
async def get_public_party(party_id: uuid.UUID, session: SessionDep) -> PartyPublic:
    """Public: what the guest form shows. Anyone with the link can call this."""
    party = await get_party_or_404(session, party_id)
    return PartyPublic(
        id=party.id,
        name=party.name,
        party_at=party.party_at,
        rsvp_deadline=party.rsvp_deadline,
        accepting_responses=accepting_responses(party),
    )


@router.post("/{party_id}/responses", status_code=status.HTTP_201_CREATED)
async def submit_response(
    party_id: uuid.UUID, body: GuestResponseCreate, session: SessionDep
) -> GuestResponseCreated:
    """Public: a guest submits the form. No login."""
    party = await get_party_or_404(session, party_id)
    if not accepting_responses(party):
        # 409 Conflict: the request is valid, but the party's current state doesn't allow it.
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="This party is no longer taking responses"
        )

    response = GuestResponse(party_id=party.id, **body.model_dump())
    session.add(response)
    await session.commit()

    log.info("guest response saved", extra={"party_id": str(party.id)})  # no guest name: PII
    return GuestResponseCreated(id=response.id, party_id=party.id, name=response.name)
