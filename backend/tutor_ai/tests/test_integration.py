"""Integration tests for complete API workflow with LangChain integration.

This module tests end-to-end functionality of the chat and start message endpoints,
ensuring proper integration between FastAPI, LangChain client, and response parsing.
Professional-grade tests with comprehensive mocking for fast, reliable execution.
"""

import os
import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from tutor_ai.chat.schemas import ChatResponse, StartMessageResponse
from tutor_ai.enums import ErrorType
from tutor_ai.errors import LLMError


class TestEndToEndChatWorkflow:
    """Test complete chat workflow integration with mocked LangChain processing."""

    @pytest.mark.asyncio
    async def test_chat_endpoint_with_grammar_error_returns_corrections(
        self,
        client: TestClient,
        mock_langchain_client: MagicMock,
        mock_helper: type,
        valid_chat_request_data: dict[str, str],
    ) -> None:
        """Test chat endpoint processes grammar errors and returns structured corrections."""
        # Configure mock to return grammar error response
        mock_helper.configure_response(mock_langchain_client, "grammar_error")

        request_data = valid_chat_request_data.copy()
        request_data["message"] = "I have important meeting tomorrow and I need practice my presentation skills"

        response = client.post("/api/v1/chat", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Validate response structure matches ChatResponse schema
        chat_response = ChatResponse.model_validate(data)

        # Verify AI provides feedback about the grammar error
        assert chat_response.ai_response
        assert len(chat_response.ai_response.strip()) > 0

        # Verify corrections are provided for the grammar error
        assert len(chat_response.corrections) > 0
        correction = chat_response.corrections[0]
        assert correction.error_type == ErrorType.GRAMMAR
        assert "meeting" in correction.original.lower()
        assert "an important meeting" in correction.corrected.lower() or "to practice" in correction.corrected.lower()

        # Verify next phrase continues conversation
        assert chat_response.next_phrase
        assert len(chat_response.next_phrase.strip()) > 0

        # Verify session and token tracking
        assert chat_response.session_id == request_data["session_id"]
        assert chat_response.tokens_used > 0

    @pytest.mark.asyncio
    async def test_chat_endpoint_with_perfect_message_no_corrections(
        self,
        client: TestClient,
        mock_langchain_client: MagicMock,
        mock_helper: type,
        valid_chat_request_data: dict[str, str],
    ) -> None:
        """Test chat endpoint handles perfect messages without corrections."""
        # Configure mock to return perfect message response
        mock_helper.configure_response(mock_langchain_client, "perfect_message")

        request_data = valid_chat_request_data.copy()
        request_data["message"] = "My company is growing fast"

        response = client.post("/api/v1/chat", json=request_data)

        assert response.status_code == 200
        data = response.json()

        chat_response = ChatResponse.model_validate(data)

        # Verify positive feedback for correct message
        assert chat_response.ai_response
        assert any(
            word in chat_response.ai_response.lower() for word in ["correct", "good", "great", "well", "perfect"]
        )

        # Verify no corrections for perfect message
        assert len(chat_response.corrections) == 0

        # Verify conversation continues with next phrase
        assert chat_response.next_phrase
        assert chat_response.tokens_used > 0

    @pytest.mark.parametrize(
        "test_case",
        [
            {
                "language": "english",
                "message": "I recieve emails every day",
                "response_key": "spelling_error",
                "expected_error": ErrorType.SPELLING,
                "error_word": "recieve",
            },
            {
                "language": "polish",
                "message": "Moja firmy rozwija się szybko",
                "response_key": "polish_grammar",
                "expected_error": ErrorType.GRAMMAR,
                "error_word": "Moja",
            },
            {
                "language": "ukrainian",
                "message": "Моя компанія швидко розвиваються",
                "response_key": "ukrainian_grammar",
                "expected_error": ErrorType.GRAMMAR,
                "error_word": "розвиваються",
            },
        ],
        ids=lambda case: f"{case['language']}_{case['expected_error'].value}",
    )
    @pytest.mark.asyncio
    async def test_multilingual_chat_endpoints_work(
        self,
        test_case: dict,
        client: TestClient,
        mock_langchain_client: MagicMock,
        mock_helper: type,
        valid_chat_request_data: dict[str, str],
    ) -> None:
        """Test chat endpoint works across all supported languages."""
        # Configure mock for specific language response
        mock_helper.configure_response(mock_langchain_client, test_case["response_key"])

        request_data = valid_chat_request_data.copy()
        request_data.update(
            {
                "message": test_case["message"],
                "language": test_case["language"],
                "session_id": str(uuid.uuid4()),  # New session for each test
            }
        )

        response = client.post("/api/v1/chat", json=request_data)

        assert response.status_code == 200, f"Failed for {test_case['language']}"
        data = response.json()

        chat_response = ChatResponse.model_validate(data)

        # Verify language-specific processing
        assert len(chat_response.corrections) > 0, f"No corrections for {test_case['language']}"
        correction = chat_response.corrections[0]
        assert correction.error_type == test_case["expected_error"]
        assert test_case["error_word"] in correction.original

    @pytest.mark.manual
    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("REAL_OPENAI_API_KEY"),
        reason="Real OpenAI API key not provided. Set REAL_OPENAI_API_KEY to run this test manually.",
    )
    @pytest.mark.asyncio
    async def test_real_chat_endpoint_integration(self) -> None:
        """Manual test for complete chat endpoint workflow with real OpenAI API.

        This test validates the entire end-to-end HTTP → LangChain → parsing pipeline
        against the real OpenAI API to ensure production readiness.

        To run this test manually:
        1. Set REAL_OPENAI_API_KEY=sk-your-real-api-key
        2. Run: pytest -m manual backend/tests/test_integration.py::TestEndToEndChatWorkflow::\
           test_real_chat_endpoint_integration -v

        Note: This test makes actual API calls and will consume OpenAI tokens.
        """
        from tutor_ai.config import AppConfig
        from tutor_ai.dependencies import get_config
        from tutor_ai.main import create_app

        # Use real API key from environment, bypassing test fixtures
        real_api_key = os.getenv("REAL_OPENAI_API_KEY")

        # Create app with real API key configuration
        with patch.dict(os.environ, {"OPENAI_API_KEY": real_api_key}, clear=False):
            # Create fresh app instance with real configuration
            config = AppConfig(_env_file=None)
            app = create_app()
            app.dependency_overrides[get_config] = lambda: config

            with TestClient(app) as client:
                # Test realistic chat request that should trigger corrections
                request_data = {
                    "message": "I have meeting tomorrow and I need practice my presentation skills",
                    "language": "english",
                    "level": "B2",
                    "session_id": str(uuid.uuid4()),
                }

                try:
                    # Make actual HTTP request to chat endpoint
                    response = client.post("/api/v1/chat", json=request_data)

                    # Validate HTTP response
                    assert response.status_code == 200, f"HTTP request failed: {response.status_code} - {response.text}"
                    assert response.headers["content-type"] == "application/json"

                    # Parse and validate response structure
                    data = response.json()
                    chat_response = ChatResponse.model_validate(data)

                    # Validate core response fields
                    assert chat_response.ai_response, "AI response should not be empty"
                    assert len(chat_response.ai_response.strip()) > 0, "AI response should contain content"
                    assert chat_response.next_phrase, "Next phrase should not be empty"
                    assert len(chat_response.next_phrase.strip()) > 0, "Next phrase should contain content"
                    assert chat_response.tokens_used > 0, "Token usage should be tracked"
                    assert chat_response.session_id == request_data["session_id"], "Session ID should match"

                    # Print response for manual inspection
                    print("\n=== REAL API INTEGRATION TEST RESULTS ===")
                    print(f"AI Response: {chat_response.ai_response}")
                    print(f"Next Phrase: {chat_response.next_phrase}")
                    print(f"Corrections found: {len(chat_response.corrections)}")
                    print(f"Token Usage: {chat_response.tokens_used}")

                    # Validate corrections
                    print(f"Sample correction: {chat_response.corrections[0].corrected}")
                    # Validate correction structure
                    correction = chat_response.corrections[0]
                    assert correction.original, "Correction original text should not be empty"
                    assert correction.corrected, "Correction corrected text should not be empty"
                    assert correction.explanation, "Correction explanation should not be empty"
                    assert correction.error_type, "Correction error type should be specified"
                    print(f"Error type: {correction.error_type}")
                    print(f"Explanation: {correction.explanation}")

                    print("=== TEST COMPLETED SUCCESSFULLY ===\n")

                except Exception as e:
                    pytest.fail(f"Real API integration test failed: {e}")


class TestStartMessageEndpoint:
    """Test AI tutor greeting generation functionality."""

    @pytest.mark.asyncio
    async def test_start_endpoint_generates_appropriate_greeting(
        self,
        client: TestClient,
        mock_langchain_client: MagicMock,
        mock_helper: type,
        valid_start_request_data: dict[str, str],
    ) -> None:
        """Test start endpoint generates language/level appropriate greeting."""
        # Configure mock to return English start message
        mock_helper.configure_response(mock_langchain_client, "start_message_english")

        response = client.post("/api/v1/start", json=valid_start_request_data)

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        start_response = StartMessageResponse.model_validate(data)

        # Verify greeting message is contextual and appropriate
        assert start_response.message
        assert len(start_response.message.strip()) > 0

        # Verify greeting mentions tutoring/practice context
        message_lower = start_response.message.lower()
        assert any(word in message_lower for word in ["tutor", "practice", "language", "learn", "help"])

        # Verify session and token tracking
        assert start_response.session_id == valid_start_request_data["session_id"]
        assert start_response.tokens_used > 0

    @pytest.mark.parametrize(
        "language_case",
        [
            {
                "language": "english",
                "response_key": "start_message_english",
                "expected_words": ["hello", "welcome", "practice", "english"],
            },
            {
                "language": "polish",
                "response_key": "start_message_polish",
                "expected_words": ["cześć", "witaj", "język", "polski"],
            },
            {
                "language": "ukrainian",
                "response_key": "start_message_ukrainian",
                "expected_words": ["привіт", "вітаю", "мова", "український"],
            },
        ],
        ids=lambda case: f"start_message_{case['language']}",
    )
    @pytest.mark.asyncio
    async def test_start_endpoint_multilingual_greetings(
        self,
        language_case: dict,
        client: TestClient,
        mock_langchain_client: MagicMock,
        mock_helper: type,
        valid_start_request_data: dict[str, str],
    ) -> None:
        """Test start messages in all supported languages are appropriate."""
        # Configure mock for specific language
        mock_helper.configure_response(mock_langchain_client, language_case["response_key"])

        request_data = valid_start_request_data.copy()
        request_data.update(
            {
                "language": language_case["language"],
                "session_id": str(uuid.uuid4()),  # New session for each language
            }
        )

        response = client.post("/api/v1/start", json=request_data)

        assert response.status_code == 200, f"Failed for {language_case['language']}"
        data = response.json()

        start_response = StartMessageResponse.model_validate(data)
        message_lower = start_response.message.lower()

        # Verify at least one language-appropriate word is present
        assert any(word in message_lower for word in language_case["expected_words"]), (
            f"No appropriate words found in {language_case['language']} greeting: {start_response.message}"
        )


class TestChatEndpointErrorHandling:
    """Test chat endpoint error scenarios and validation."""

    @pytest.mark.parametrize(
        "invalid_request",
        [
            {
                "message": "",  # Empty message
                "language": "english",
                "level": "B2",
                "session_id": str(uuid.uuid4()),
            },
            {
                "message": "test message",
                "language": "invalid_language",  # Invalid language
                "level": "B2",
                "session_id": str(uuid.uuid4()),
            },
            {
                "message": "test message",
                "language": "english",
                "level": "Z9",  # Invalid level
                "session_id": str(uuid.uuid4()),
            },
            {
                "message": "test message",
                "language": "english",
                "level": "B2",
                "session_id": "not-a-uuid",  # Invalid UUID format
            },
            {
                "message": "test message",
                "language": "english",
                "level": "B2",
                # Missing session_id
            },
        ],
        ids=["empty_message", "invalid_language", "invalid_level", "invalid_uuid", "missing_session_id"],
    )
    def test_chat_endpoint_invalid_request_schema_validation(
        self, invalid_request: dict, client: TestClient, mock_langchain_client: MagicMock
    ) -> None:
        """Test chat endpoint validates request schema properly."""
        response = client.post("/api/v1/chat", json=invalid_request)

        assert response.status_code == 422, f"Expected 422 for {invalid_request}"
        error_data = response.json()
        assert "detail" in error_data
        assert isinstance(error_data["detail"], list)

    @pytest.mark.asyncio
    async def test_chat_endpoint_langchain_api_failure_handling(
        self,
        client: TestClient,
        mock_langchain_client: MagicMock,
        mock_helper: type,
        valid_chat_request_data: dict[str, str],
    ) -> None:
        """Test chat endpoint handles LangChain/OpenAI API failures gracefully."""
        # Configure mock to raise LLM error
        mock_helper.configure_error(mock_langchain_client, LLMError, "OpenAI API rate limit exceeded")

        response = client.post("/api/v1/chat", json=valid_chat_request_data)

        assert response.status_code == 503
        error_data = response.json()
        # FastAPI returns HTTPException detail directly
        assert error_data["detail"]["error"] == "Service temporarily unavailable"
        assert "rate limit" in error_data["detail"]["message"].lower()

    @pytest.mark.asyncio
    async def test_chat_endpoint_malformed_ai_response_fallback(
        self,
        client: TestClient,
        mock_langchain_client: MagicMock,
        mock_helper: type,
        valid_chat_request_data: dict[str, str],
    ) -> None:
        """Test chat endpoint handles malformed AI responses via CorrectionParser fallback."""
        # Configure mock to return malformed response
        mock_helper.configure_malformed_response(mock_langchain_client, "This is not valid JSON or expected format")

        response = client.post("/api/v1/chat", json=valid_chat_request_data)

        # Should still return 200 with fallback response
        assert response.status_code == 200
        data = response.json()

        chat_response = ChatResponse.model_validate(data)

        # Verify fallback values are used (as implemented in CorrectionParser)
        assert chat_response.ai_response  # Should have fallback
        assert chat_response.next_phrase  # Should have fallback
        assert len(chat_response.corrections) == 0  # No corrections from malformed response


class TestAPIResponseStructure:
    """Test API response structure compliance with Pydantic schemas."""

    @pytest.mark.asyncio
    async def test_chat_response_matches_schema_exactly(
        self, client: TestClient, mock_langchain_client: MagicMock, valid_chat_request_data: dict[str, str]
    ) -> None:
        """Test ChatResponse structure matches Pydantic schema exactly."""
        response = client.post("/api/v1/chat", json=valid_chat_request_data)

        assert response.status_code == 200
        data = response.json()

        # Validate against schema - will raise exception if invalid
        chat_response = ChatResponse.model_validate(data)

        # Verify all required fields are present
        required_fields = ["ai_response", "next_phrase", "corrections", "session_id", "tokens_used"]
        for field in required_fields:
            assert hasattr(chat_response, field)
            assert getattr(chat_response, field) is not None

    @pytest.mark.asyncio
    async def test_start_response_matches_schema_exactly(
        self, client: TestClient, mock_langchain_client: MagicMock, valid_start_request_data: dict[str, str]
    ) -> None:
        """Test StartMessageResponse structure matches schema exactly."""
        response = client.post("/api/v1/start", json=valid_start_request_data)

        assert response.status_code == 200
        data = response.json()

        # Validate against schema
        start_response = StartMessageResponse.model_validate(data)

        # Verify all required fields are present
        required_fields = ["message", "session_id", "tokens_used"]
        for field in required_fields:
            assert hasattr(start_response, field)
            assert getattr(start_response, field) is not None


class TestTokenUsageTracking:
    """Test token usage is properly tracked and returned in responses."""

    @pytest.mark.asyncio
    async def test_chat_endpoint_tracks_token_usage_accurately(
        self, client: TestClient, mock_langchain_client: MagicMock, valid_chat_request_data: dict[str, str]
    ) -> None:
        """Test chat endpoint returns accurate token usage from LangChain."""
        request_data = valid_chat_request_data.copy()
        request_data["message"] = "This is a longer message that should consume more tokens for processing"

        response = client.post("/api/v1/chat", json=request_data)

        assert response.status_code == 200
        data = response.json()

        chat_response = ChatResponse.model_validate(data)

        # Verify token usage is tracked and reasonable
        assert chat_response.tokens_used > 0
        assert chat_response.tokens_used < 1000  # Reasonable upper bound for simple message

    @pytest.mark.asyncio
    async def test_start_endpoint_tracks_token_usage_accurately(
        self, client: TestClient, mock_langchain_client: MagicMock, valid_start_request_data: dict[str, str]
    ) -> None:
        """Test start endpoint returns accurate token usage."""
        response = client.post("/api/v1/start", json=valid_start_request_data)

        assert response.status_code == 200
        data = response.json()

        start_response = StartMessageResponse.model_validate(data)

        # Verify token usage is tracked for start message generation
        assert start_response.tokens_used > 0
        assert start_response.tokens_used < 500  # Start messages should be relatively short
