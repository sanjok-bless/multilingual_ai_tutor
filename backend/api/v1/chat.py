"""Chat endpoint for multilingual AI tutoring interactions."""

from fastapi import APIRouter

from backend.dependencies import ConfigDep

router = APIRouter()


@router.post("/chat")
async def chat_endpoint() -> dict:
    """Main chat endpoint for AI tutoring sessions."""
    return {}


@router.get("/languages")
async def get_languages(config: ConfigDep) -> list[str]:
    """Get supported languages."""
    return config.supported_languages
