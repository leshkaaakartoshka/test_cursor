"""Health check endpoint."""

from fastapi import APIRouter, Depends
from app.models.schemas import HealthResponse
from app.core.config import Settings, get_settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(settings: Settings = Depends(get_settings)):
    """Health check endpoint."""
    return HealthResponse()