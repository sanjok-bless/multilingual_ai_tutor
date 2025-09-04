"""Health check endpoint for monitoring service availability."""

import time

from fastapi import APIRouter

from backend.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="healthy", message="Multilingual AI Tutor is running", timestamp=int(time.time()))
