"""Party endpoints."""

from fastapi import APIRouter, status

from app.auth import CurrentUser
from app.config import get_settings
from app.db import SessionDep
from app.log import get_logger
from app.models import Party
from app.schemas.party import PartyCreate, PartyCreated

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

    frontend = get_settings().frontend_origin.rstrip("/")
    return PartyCreated(
        id=party.id,
        name=party.name,
        party_at=party.party_at,
        status=party.status,
        guest_url=f"{frontend}/p/{party.id}",
    )
