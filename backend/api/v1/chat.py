"""Chat endpoint for multilingual AI tutoring interactions."""

from fastapi import APIRouter, HTTPException

from backend.chat.schemas import ChatRequest, ChatResponse, StartMessageRequest, StartMessageResponse
from backend.dependencies import ConfigDep, LangChainDep
from backend.errors import LLMError
from backend.schemas import ConfigResponse

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


@router.get("/config", response_model=ConfigResponse)
async def get_config(config: ConfigDep) -> ConfigResponse:
    """Get application configuration including supported languages and context limits."""
    return ConfigResponse(
        languages=config.supported_languages,
        context_chat_limit=config.context_chat_messages_num * 2,
        context_start_limit=config.context_start_messages_num * 2,
    )
