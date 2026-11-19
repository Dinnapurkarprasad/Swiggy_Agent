from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_settings
from app.models.enums import SwiggyMode

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    swiggy_mode: SwiggyMode


@router.get("/health")
async def health() -> HealthResponse:
    return HealthResponse(status="ok", swiggy_mode=get_settings().swiggy_mode)
