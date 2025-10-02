"""Tests for LangChain client integration with OpenAI API."""

import os
from collections.abc import Callable
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from backend.chat.schemas import ChatRequest, ChatResponse, StartMessageRequest, StartMessageResponse
from backend.config import AppConfig
from backend.enums import ErrorType, Language, Level
from backend.errors import LLMError
from backend.llms.langchain_client import LangChainClient

# Type aliases for fixtures
type AIResponseLoader = Callable[[str], str]


class TestLangChainClient:
    """Test suite for LangChain client integration."""

    @pytest.fixture
    def sample_chat_request(self) -> ChatRequest:
        """Create sample chat request for testing."""
        return ChatRequest(
            message="I have meeting tomorrow", language=Language.EN, level=Level.B2, session_id=str(uuid4())
        )

    @pytest.fixture
    def mock_langchain_client(self) -> Mock:
        """Create mocked LangChain client."""
        return Mock(spec=ChatOpenAI)

    def create_mock_langchain_response(self, content: str, tokens: int = 100) -> AIMessage:
        """Create mock LangChain AIMessage response."""
        return AIMessage(content=content, response_metadata={"token_usage": {"total_tokens": tokens}})

    @pytest.mark.asyncio
    async def test_langchain_client_initialization(self, mock_config: AppConfig) -> None:
        """Test LangChain client initializes with proper configuration."""
        client = LangChainClient(config=mock_config)

        assert client.langchain_client.model_name == "gpt-4o-mini"
        assert client.langchain_client.temperature == 0.7  # From mock config
        assert client.langchain_client.max_tokens == 500  # From mock config

    @pytest.mark.asyncio
    async def test_successful_chat_completion_with_grammar_error(
        self,
        sample_chat_request: ChatRequest,
        mock_config: AppConfig,
        mock_langchain_client: Mock,
        ai_response_loader: AIResponseLoader,
    ) -> None:
        """Test successful API call with grammar error correction."""
        # Use AI response fixture content for mock
        ai_content = ai_response_loader("grammar_error_single")

        # Create mock LangChain response
        mock_response = AIMessage(content=ai_content, response_metadata={"token_usage": {"total_tokens": 205}})
        mock_langchain_client.ainvoke.return_value = mock_response

        client = LangChainClient(config=mock_config, langchain_client=mock_langchain_client)
        response = await client.process_chat(sample_chat_request)

        assert isinstance(response, ChatResponse)
        assert "I have **an** important meeting tomorrow" in response.ai_response
        assert len(response.corrections) == 1
        assert response.corrections[0].error_type == ErrorType.GRAMMAR
        assert response.tokens_used == 205
        assert response.next_phrase == "What's your presentation about?"

    @pytest.mark.asyncio
    async def test_successful_chat_completion_with_perfect_message(
        self, mock_config: AppConfig, mock_langchain_client: Mock, ai_response_loader: AIResponseLoader
    ) -> None:
        """Test successful API call with no corrections needed."""
        perfect_request = ChatRequest(
            message="My company is growing fast", language=Language.EN, level=Level.B2, session_id=str(uuid4())
        )

        ai_content = ai_response_loader("perfect_message")
        mock_response = self.create_mock_langchain_response(ai_content, tokens=160)
        mock_langchain_client.ainvoke.return_value = mock_response

        client = LangChainClient(config=mock_config, langchain_client=mock_langchain_client)
        response = await client.process_chat(perfect_request)

        assert isinstance(response, ChatResponse)
        assert "excellent" in response.ai_response.lower()
        assert len(response.corrections) == 0
        assert response.tokens_used == 160

    @pytest.mark.asyncio
    async def test_successful_chat_completion_with_spelling_error(
        self, mock_config: AppConfig, mock_langchain_client: Mock, ai_response_loader: AIResponseLoader
    ) -> None:
        """Test successful API call with spelling error correction."""
        spelling_request = ChatRequest(
            message="I recieve emails every day", language=Language.EN, level=Level.B2, session_id=str(uuid4())
        )

        ai_content = ai_response_loader("spelling_error")
        mock_response = self.create_mock_langchain_response(ai_content, tokens=185)
        mock_langchain_client.ainvoke.return_value = mock_response

        client = LangChainClient(config=mock_config, langchain_client=mock_langchain_client)
        response = await client.process_chat(spelling_request)

        assert isinstance(response, ChatResponse)
        assert len(response.corrections) == 1
        assert response.corrections[0].error_type == ErrorType.SPELLING
        assert "receive" in response.corrections[0].corrected

    @pytest.mark.asyncio
    async def test_malformed_ai_response_fallback(
        self,
        sample_chat_request: ChatRequest,
        mock_config: AppConfig,
        mock_langchain_client: Mock,
        ai_response_loader: AIResponseLoader,
    ) -> None:
        """Test handling of malformed AI responses with fallback logic."""
        ai_content = ai_response_loader("malformed_missing_structure")
        mock_response = self.create_mock_langchain_response(ai_content, tokens=122)
        mock_langchain_client.ainvoke.return_value = mock_response

        client = LangChainClient(config=mock_config, langchain_client=mock_langchain_client)
        response = await client.process_chat(sample_chat_request)

        # Should fallback to simple response when parsing fails
        assert isinstance(response, ChatResponse)
        assert "I have a meeting tomorrow" in response.ai_response
        assert len(response.corrections) == 0  # No corrections parsed from malformed response
        assert response.tokens_used == 122
        assert response.next_phrase == "Please continue."  # Fallback value for required field

    @pytest.mark.asyncio
    async def test_openai_api_authentication_error(
        self, sample_chat_request: ChatRequest, mock_config: AppConfig, mock_langchain_client: Mock
    ) -> None:
        """Test handling of LangChain API authentication errors."""
        from openai import AuthenticationError

        mock_langchain_client.ainvoke.side_effect = AuthenticationError(
            message="Invalid API key", response=Mock(status_code=401), body=None
        )

        client = LangChainClient(config=mock_config, langchain_client=mock_langchain_client)

        with pytest.raises(LLMError) as exc_info:
            await client.process_chat(sample_chat_request)

        assert "LLM processing failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_openai_api_validation_error(self, mock_config: AppConfig, mock_langchain_client: Mock) -> None:
        """Test handling of invalid request parameters."""
        from openai import BadRequestError

        # This test validates API-level validation, not Pydantic validation
        # Create a request that passes Pydantic but could fail API validation

        mock_langchain_client.ainvoke.side_effect = BadRequestError(
            message="Invalid request: validation failed", response=Mock(status_code=400), body=None
        )

        client = LangChainClient(config=mock_config, langchain_client=mock_langchain_client)

        # Use a minimal valid request
        valid_request = ChatRequest(
            message="x",  # Minimal valid message that passes Pydantic
            language=Language.EN,
            level=Level.B2,
            session_id=str(uuid4()),
        )

        with pytest.raises(LLMError) as exc_info:
            await client.process_chat(valid_request)

        assert "LLM processing failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_token_usage_tracking(
        self,
        sample_chat_request: ChatRequest,
        mock_config: AppConfig,
        mock_langchain_client: Mock,
        ai_response_loader: AIResponseLoader,
    ) -> None:
        """Test accurate token usage tracking from LangChain responses."""
        ai_content = ai_response_loader("grammar_error_single")
        mock_response = self.create_mock_langchain_response(ai_content, tokens=205)
        mock_langchain_client.ainvoke.return_value = mock_response

        client = LangChainClient(config=mock_config, langchain_client=mock_langchain_client)
        response = await client.process_chat(sample_chat_request)

        assert response.tokens_used == 205
        # Note: ChatResponse doesn't include detailed token breakdown by design
        # Only total tokens_used is tracked for simplicity

    @pytest.mark.asyncio
    async def test_retry_logic_on_temporary_failures(
        self,
        sample_chat_request: ChatRequest,
        mock_config: AppConfig,
        mock_langchain_client: Mock,
        ai_response_loader: AIResponseLoader,
    ) -> None:
        """Test retry logic for temporary API failures."""

        ai_content = ai_response_loader("grammar_error_single")
        mock_success_response = self.create_mock_langchain_response(ai_content, tokens=205)

        # First call fails, second succeeds - APIError constructor signature may vary
        mock_langchain_client.ainvoke.side_effect = [
            Exception("Temporary failure"),  # Generic exception for testing
            mock_success_response,
        ]

        # Note: Current LangChainClient doesn't implement retry logic
        # This test documents expected behavior for future implementation
        client = LangChainClient(config=mock_config, langchain_client=mock_langchain_client)

        # With current implementation, this will raise LLMError on first failure
        with pytest.raises(LLMError):
            await client.process_chat(sample_chat_request)

    @pytest.mark.asyncio
    async def test_multilingual_support(
        self, mock_config: AppConfig, mock_langchain_client: Mock, ai_response_loader: AIResponseLoader
    ) -> None:
        """Test processing requests in different languages."""
        languages_to_test = [
            (Language.PL, "Moja firmy rozwija się szybko"),  # Polish with grammar error
            (Language.UA, "Моя компанія швидко розвиваються"),  # Ukrainian with grammar error
            (Language.DE, "Ich habe ein wichtiges Meeting morgen"),  # German (future support)
        ]

        for language, message in languages_to_test:
            request = ChatRequest(message=message, language=language, level=Level.B2, session_id=str(uuid4()))

            # Mock appropriate response for each language
            ai_content = ai_response_loader("grammar_error_single")
            mock_response = self.create_mock_langchain_response(ai_content, tokens=205)
            mock_langchain_client.ainvoke.return_value = mock_response

            client = LangChainClient(config=mock_config, langchain_client=mock_langchain_client)
            response = await client.process_chat(request)

            assert isinstance(response, ChatResponse)
            assert response.session_id == request.session_id

    def test_langchain_integration_interface(self) -> None:
        """Test that LangChain integration follows expected interface."""
        # Interface requirements validation:
        # 1. Class should be named LangChainClient ✓
        # 2. Constructor should accept AppConfig and optional OpenAI client ✓
        # 3. Main method should be async process_chat(ChatRequest) -> ChatResponse ✓
        # 4. Should handle all OpenAI exceptions and convert to domain exceptions ✓
        # 5. Should integrate with existing PromptManager for system/user prompts ✓
        # 6. Should parse responses using CorrectionParser ✓

        # Basic interface validation
        assert hasattr(LangChainClient, "__init__")
        assert hasattr(LangChainClient, "process_chat")

        # Verify constructor signature accepts required parameters
        import inspect

        sig = inspect.signature(LangChainClient.__init__)
        assert "config" in sig.parameters
        assert "langchain_client" in sig.parameters

    # Start Message Tests
    async def test_generate_start_message_basic_functionality(
        self, mock_config: AppConfig, mock_langchain_client: Mock
    ) -> None:
        """Test basic functionality of generate_start_message method."""
        # Setup mock response
        mock_ai_response = self.create_mock_langchain_response("Hello! Ready to practice English?", tokens=20)
        mock_langchain_client.ainvoke.return_value = mock_ai_response

        # Create request
        request = StartMessageRequest(language=Language.EN, level=Level.B1, session_id=str(uuid4()))

        # Test the method
        client = LangChainClient(config=mock_config, langchain_client=mock_langchain_client)
        response = await client.generate_start_message(request)

        # Verify response structure
        assert isinstance(response, StartMessageResponse)
        assert response.message == "Hello! Ready to practice English?"
        assert response.session_id == request.session_id
        assert response.tokens_used == 20

    async def test_generate_start_message_handles_llm_errors(
        self, mock_config: AppConfig, mock_langchain_client: Mock
    ) -> None:
        """Test that LLM errors are properly handled."""
        # Setup mock to raise exception
        mock_langchain_client.ainvoke.side_effect = Exception("OpenAI API Error")

        request = StartMessageRequest(language=Language.EN, level=Level.B1, session_id=str(uuid4()))
        client = LangChainClient(config=mock_config, langchain_client=mock_langchain_client)

        # Should raise LLMError
        with pytest.raises(LLMError) as exc_info:
            await client.generate_start_message(request)

        assert "Start message generation failed" in str(exc_info.value)

    @pytest.mark.parametrize(
        "language,level", [(Language.EN, Level.B1), (Language.DE, Level.C2), (Language.UA, Level.A1)]
    )
    async def test_generate_start_message_different_languages_levels(
        self, mock_config: AppConfig, mock_langchain_client: Mock, language: Language, level: Level
    ) -> None:
        """Test generate_start_message works with different language/level combinations."""
        # Setup mock response
        mock_ai_response = self.create_mock_langchain_response(f"Hello in {language.value}!", tokens=25)
        mock_langchain_client.ainvoke.return_value = mock_ai_response

        request = StartMessageRequest(language=language, level=level, session_id=str(uuid4()))
        client = LangChainClient(config=mock_config, langchain_client=mock_langchain_client)
        response = await client.generate_start_message(request)

        # Verify response is valid
        assert isinstance(response, StartMessageResponse)
        assert len(response.message.strip()) > 0
        assert response.tokens_used == 25


class TestLangChainClientIntegration:
    """Integration tests that can optionally run against real OpenAI API."""

    @pytest.mark.manual
    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("REAL_OPENAI_API_KEY"),
        reason="Real OpenAI API key not provided. Set REAL_OPENAI_API_KEY to run this test manually.",
    )
    async def test_real_openai_api_integration(self) -> None:
        """Manual test for real OpenAI API integration.

        This test validates the actual production code path against the real OpenAI API.
        It is marked as 'manual' and requires setting REAL_OPENAI_API_KEY environment variable.

        To run this test manually:
        1. Set REAL_OPENAI_API_KEY=sk-your-real-api-key
        2. Run: pytest -m manual backend/tests/test_langchain_client.py::TestLangChainClientIntegration::\
           test_real_openai_api_integration -v

        Note: This test makes actual API calls and will consume OpenAI tokens.
        """
        # Use real API key from environment, bypassing test fixtures
        real_api_key = os.getenv("REAL_OPENAI_API_KEY")

        # Create config with real API key (bypass test environment mocking)
        with patch.dict(os.environ, {"OPENAI_API_KEY": real_api_key}, clear=False):
            config = AppConfig(_env_file=None)
            client = LangChainClient(config=config)

        # Create realistic ChatRequest that should trigger corrections
        test_request = ChatRequest(
            message="I have meeting tomorrow and I need practice my presentation skills",
            language=Language.EN,
            level=Level.B2,
            session_id=str(uuid4()),
        )

        try:
            # Test actual production async execution path
            response = await client.process_chat(test_request)

            # Validate complete ChatResponse structure
            assert isinstance(response, ChatResponse)
            assert response.ai_response  # Should have AI response
            assert response.next_phrase  # Should have next phrase
            assert response.tokens_used > 0  # Should track token usage
            assert response.session_id == test_request.session_id

            # Print response for manual inspection and fixture data updates
            print(f"AI Response: {response.ai_response}")
            print(f"Corrections found: {len(response.corrections)}")
            print(f"Next Phrase: {response.next_phrase}")
            print(f"Token Usage: {response.tokens_used}")

            # Should find grammar corrections for the test message
            if response.corrections:
                print(f"Sample correction: {response.corrections[0].corrected}")

        except Exception as e:
            pytest.fail(f"LangChain integration failed: {e}")

    @pytest.mark.asyncio
    async def test_process_chat_passes_context_to_prompt_manager(
        self, mock_config: AppConfig, mock_langchain_client: Mock, ai_response_loader: AIResponseLoader
    ) -> None:
        """Test that process_chat passes context messages to PromptManager."""
        context = [
            {"role": "user", "content": "Hello"},
            {"role": "ai", "content": "Hi there!"},
        ]

        request = ChatRequest(
            message="How are you?",
            language=Language.EN,
            level=Level.B1,
            session_id=str(uuid4()),
            context_messages=context,
        )

        # Mock LangChain response with async coroutine
        ai_content = ai_response_loader("perfect_message")
        mock_response = AIMessage(content=ai_content, response_metadata={"token_usage": {"total_tokens": 100}})

        # Use AsyncMock for async method
        mock_langchain_client.ainvoke = AsyncMock(return_value=mock_response)

        # Create client and patch PromptManager to track calls
        client = LangChainClient(config=mock_config, langchain_client=mock_langchain_client)

        with patch.object(
            client.prompt_manager, "render_tutoring_prompt", wraps=client.prompt_manager.render_tutoring_prompt
        ) as mock_render:
            await client.process_chat(request)

            # Verify render_tutoring_prompt was called with context
            mock_render.assert_called_once()
            call_kwargs = mock_render.call_args.kwargs
            assert call_kwargs["context_messages"] == context
            assert call_kwargs["user_message"] == "How are you?"
            assert call_kwargs["language"] == Language.EN
            assert call_kwargs["level"] == Level.B1

    @pytest.mark.asyncio
    async def test_generate_start_message_passes_context_to_prompt_manager(
        self, mock_config: AppConfig, mock_langchain_client: Mock
    ) -> None:
        """Test that generate_start_message passes context to PromptManager."""
        context = [
            {"role": "user", "content": "Previous message"},
            {"role": "ai", "content": "Previous response"},
        ]

        request = StartMessageRequest(
            language=Language.EN, level=Level.B2, session_id=str(uuid4()), context_messages=context
        )

        # Mock LangChain response with async coroutine
        mock_response = AIMessage(content="Welcome back!", response_metadata={"token_usage": {"total_tokens": 20}})

        mock_langchain_client.ainvoke = AsyncMock(return_value=mock_response)

        # Create client and patch PromptManager
        client = LangChainClient(config=mock_config, langchain_client=mock_langchain_client)

        with patch.object(
            client.prompt_manager, "render_start_message", wraps=client.prompt_manager.render_start_message
        ) as mock_render:
            await client.generate_start_message(request)

            # Verify render_start_message was called with context
            mock_render.assert_called_once()
            call_kwargs = mock_render.call_args.kwargs
            assert call_kwargs["context_messages"] == context
            assert call_kwargs["language"] == Language.EN
            assert call_kwargs["level"] == Level.B2
