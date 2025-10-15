"""LangChain client for OpenAI integration."""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from tutor_ai.chat.schemas import ChatRequest, ChatResponse, StartMessageRequest, StartMessageResponse
from tutor_ai.config import AppConfig
from tutor_ai.errors import LLMError
from tutor_ai.llms.correction_parser import CorrectionParser
from tutor_ai.llms.prompt_manager import PromptManager


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

    def _extract_tokens(self, response_metadata: dict) -> int:
        """Extract token usage with defensive parsing."""
        token_usage = response_metadata.get("token_usage", {})
        if isinstance(token_usage, dict) and "total_tokens" in token_usage:
            return max(0, int(token_usage["total_tokens"]))
        return 0

    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        """Process chat request and return structured response."""
        try:
            # Generate prompts using PromptManager
            system_prompt = self.prompt_manager.render_system_prompt(language=request.language, level=request.level)

            user_prompt = self.prompt_manager.render_tutoring_prompt(
                user_message=request.message,
                language=request.language,
                level=request.level,
                context_messages=request.context_messages,
                limit=self.config.context_chat_messages_num,
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

            # Extract token usage with defensive parsing
            tokens_used = self._extract_tokens(response.response_metadata)

            return ChatResponse(
                ai_response=ai_response,
                next_phrase=next_phrase,
                corrections=parsed_response.corrections,
                session_id=request.session_id,
                tokens_used=tokens_used,
            )

        except Exception as e:
            raise LLMError(f"LLM processing failed: {e}") from e

    async def generate_start_message(self, request: StartMessageRequest) -> StartMessageResponse:
        """Generate AI tutor start message for conversation initiation."""
        try:
            # Generate prompts using PromptManager
            system_prompt = self.prompt_manager.render_system_prompt(language=request.language, level=request.level)
            start_prompt = self.prompt_manager.render_start_message(
                language=request.language,
                level=request.level,
                context_messages=request.context_messages,
                limit=self.config.context_start_messages_num,
            )

            # Create LangChain messages
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=start_prompt)]

            # Make LangChain API call
            response = await self.langchain_client.ainvoke(messages)

            # Extract token usage with defensive parsing
            tokens_used = self._extract_tokens(response.response_metadata)

            return StartMessageResponse(
                message=response.content.strip(),
                session_id=request.session_id,
                tokens_used=tokens_used,
            )

        except Exception as e:
            raise LLMError(f"Start message generation failed: {e}") from e
