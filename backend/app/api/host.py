"""Host dashboard endpoints. Every route requires sign-in and only shows the host's own parties."""

import uuid

from fastapi import APIRouter
from sqlalchemy import func
from sqlmodel import col, select

from app.api.common import get_host_party_or_404, guest_url
from app.auth import CurrentUser
from app.db import SessionDep
from app.models import GuestResponse, Party
from app.planner.summary import summarize
from app.schemas.guest import GuestResponseOut
from app.schemas.party import PartyDetail, PartyListItem

router = APIRouter(prefix="/host", tags=["host"])


@router.get("/parties")
async def list_my_parties(host: CurrentUser, session: SessionDep) -> list[PartyListItem]:
    # One query: each of my parties + how many responses it has.
    # OUTER JOIN keeps parties with zero responses (an inner join would drop them).
    statement = (
        select(Party, func.count(col(GuestResponse.id)))
        .outerjoin(GuestResponse, col(GuestResponse.party_id) == col(Party.id))
        .where(Party.host_user_id == host.id)
        .group_by(col(Party.id))
        .order_by(col(Party.party_at).desc())
    )
    rows = (await session.exec(statement)).all()
    return [
        PartyListItem(
            id=party.id,
            name=party.name,
            party_at=party.party_at,
            status=party.status,
            response_count=count,
            guest_url=guest_url(party.id),
        )
        for party, count in rows
    ]


@router.get("/parties/{party_id}")
async def get_my_party(party_id: uuid.UUID, host: CurrentUser, session: SessionDep) -> PartyDetail:
    party = await get_host_party_or_404(session, party_id, host.id)
    responses = (
        await session.exec(
            select(GuestResponse)
            .where(GuestResponse.party_id == party.id)
            .order_by(col(GuestResponse.created_at))
        )
    ).all()

    return PartyDetail(
        id=party.id,
        name=party.name,
        party_at=party.party_at,
        rsvp_deadline=party.rsvp_deadline,
        budget_per_person_paise=party.budget_per_person_paise,
        status=party.status,
        guest_url=guest_url(party.id),
        summary=summarize(responses),
        responses=[GuestResponseOut.model_validate(r) for r in responses],
    )
