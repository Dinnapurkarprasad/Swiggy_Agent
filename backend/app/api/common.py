"""Small helpers shared by party routes."""

import uuid

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import get_settings
from app.models import Party
from app.models.base import utcnow
from app.models.enums import PartyStatus


def guest_url(party_id: uuid.UUID) -> str:
    return f"{get_settings().frontend_origin.rstrip('/')}/p/{party_id}"


def accepting_responses(party: Party) -> bool:
    """Guests may submit only while the party is collecting and before the RSVP deadline."""
    if party.status != PartyStatus.COLLECTING:
        return False
    return party.rsvp_deadline is None or utcnow() < party.rsvp_deadline


def party_not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Party not found")


async def get_party_or_404(session: AsyncSession, party_id: uuid.UUID) -> Party:
    party = await session.get(Party, party_id)
    if party is None:
        raise party_not_found()
    return party


async def get_host_party_or_404(
    session: AsyncSession, party_id: uuid.UUID, host_user_id: uuid.UUID
) -> Party:
    """The party, but only if this host owns it.

    Someone else's party returns 404 (not 403), so hosts can't probe which party ids exist.
    """
    party = await session.get(Party, party_id)
    if party is None or party.host_user_id != host_user_id:
        raise party_not_found()
    return party
