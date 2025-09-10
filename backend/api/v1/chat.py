"""Chat endpoint for multilingual AI tutoring interactions."""

from fastapi import APIRouter, HTTPException

from backend.chat.schemas import ChatRequest, ChatResponse, StartMessageRequest, StartMessageResponse
from backend.dependencies import ConfigDep, LangChainDep
from backend.errors import LLMError

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, client: LangChainDep) -> ChatResponse:
    """Main chat endpoint for AI tutoring sessions."""
    try:
        return await client.process_chat(request)
    except LLMError as e:
        raise HTTPException(
            status_code=503,
            detail={"error": "Service temporarily unavailable", "message": f"AI service error: {str(e)}"},
        ) from e


@router.post("/start", response_model=StartMessageResponse)
async def start_conversation(request: StartMessageRequest, client: LangChainDep) -> StartMessageResponse:
    """Generate AI tutor greeting to start conversation."""
    try:
        return await client.generate_start_message(request)
    except LLMError as e:
        raise HTTPException(
            status_code=503,
            detail={"error": "Service temporarily unavailable", "message": f"AI service error: {str(e)}"},
        ) from e


@router.get("/languages")
async def get_languages(config: ConfigDep) -> list[str]:
    """Get supported languages."""
    return config.supported_languages
