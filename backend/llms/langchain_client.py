"""LangChain client for OpenAI integration."""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from backend.chat.schemas import ChatRequest, ChatResponse
from backend.config import AppConfig
from backend.errors import LLMError
from backend.llms.correction_parser import CorrectionParser
from backend.llms.prompt_manager import PromptManager


class LangChainClient:
    """LangChain client wrapper for OpenAI API integration."""

    def __init__(self, config: AppConfig, langchain_client: ChatOpenAI | None = None) -> None:
        """Initialize LangChain client with configuration."""
        self.config = config
        self.langchain_client = langchain_client or ChatOpenAI(
            api_key=config.openai_api_key,
            model=config.openai_model,
            max_tokens=config.openai_max_tokens,
            temperature=config.openai_temperature,
        )
        self.prompt_manager = PromptManager()
        self.correction_parser = CorrectionParser()

    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        """Process chat request and return structured response."""
        try:
            # Generate prompts using PromptManager
            system_prompt = self.prompt_manager.render_system_prompt(language=request.language, level=request.level)

            user_prompt = self.prompt_manager.render_tutoring_prompt(
                user_message=request.message, language=request.language, level=request.level
            )

            # Create LangChain messages
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]

            # Make LangChain API call
            response = await self.langchain_client.ainvoke(messages)

            # Parse response using CorrectionParser
            parsed_response = self.correction_parser.parse_response(response.content)

            # Build ChatResponse with fallbacks for required fields
            ai_response = parsed_response.ai_response or "Response received."
            next_phrase = parsed_response.next_phrase or "Please continue."

            return ChatResponse(
                ai_response=ai_response,
                next_phrase=next_phrase,
                corrections=parsed_response.corrections,
                session_id=request.session_id,
                tokens_used=response.response_metadata.get("token_usage", {}).get("total_tokens", 0),
            )

        except Exception as e:
            raise LLMError(f"LLM processing failed: {e}") from e
