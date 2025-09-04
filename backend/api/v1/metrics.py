"""Metrics endpoint for application monitoring and observability."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/metrics")
async def metrics_endpoint() -> dict:
    """Application metrics endpoint."""
    return {}
