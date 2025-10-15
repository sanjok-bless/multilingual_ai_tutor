"""Tests for FastAPI dependency injection with LangChain client integration.

This module tests the dependency injection system for the LangChain client,
ensuring proper configuration, caching, and integration with FastAPI endpoints.
Modern Python 3.13 patterns with professional test isolation.
"""

from unittest.mock import MagicMock, patch

import pytest

from tutor_ai.config import AppConfig
from tutor_ai.dependencies import get_config, get_langchain_client
from tutor_ai.llms.langchain_client import LangChainClient


class TestLangChainDependencyInjection:
    """Test FastAPI dependency injection works correctly for LangChain client."""

    def test_get_langchain_client_dependency_returns_configured_client(self) -> None:
        """Test get_langchain_client returns properly configured LangChainClient."""
        client = get_langchain_client()

        assert isinstance(client, LangChainClient)
        assert client.config is not None
        assert isinstance(client.config, AppConfig)
        assert client.langchain_client is not None
        assert client.prompt_manager is not None
        assert client.correction_parser is not None

    def test_langchain_client_dependency_uses_app_config(self) -> None:
        """Test LangChain client dependency uses the same config as get_config."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test123456789"}):
            config = get_config()
            client = get_langchain_client()

            # Verify same configuration values
            assert client.config.openai_api_key == config.openai_api_key
            assert client.config.openai_model == config.openai_model
            assert client.config.openai_max_tokens == config.openai_max_tokens
            assert client.config.openai_temperature == config.openai_temperature

    def test_langchain_client_dependency_caching(self) -> None:
        """Test LangChain client dependency is properly cached for performance."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test123456789"}):
            # Get client multiple times
            client1 = get_langchain_client()
            client2 = get_langchain_client()
            client3 = get_langchain_client()

            # Verify same instance is returned (caching)
            assert client1 is client2
            assert client2 is client3

            # Verify underlying LangChain client is also cached
            assert client1.langchain_client is client2.langchain_client

    def test_get_langchain_client_handles_missing_api_key_gracefully(self) -> None:
        """Test get_langchain_client handles missing API key configuration."""
        with patch.dict("os.environ", {}, clear=True), patch("tutor_ai.dependencies.get_config") as mock_get_config:
            from tutor_ai.config import AppConfig

            mock_get_config.side_effect = lambda: AppConfig(_env_file=None)

            with pytest.raises(ValueError, match="Field required"):
                get_langchain_client()

    @pytest.mark.asyncio
    async def test_langchain_client_dependency_integration_methods_available(self) -> None:
        """Test LangChain client from dependency has all required methods."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test123456789"}):
            client = get_langchain_client()

            # Verify required async methods exist
            assert hasattr(client, "process_chat")
            assert callable(client.process_chat)

            assert hasattr(client, "generate_start_message")
            assert callable(client.generate_start_message)

    @pytest.mark.parametrize(
        "config",
        [
            {
                "OPENAI_API_KEY": "sk-valid123456789",
                "OPENAI_MODEL": "gpt-4o-mini",
                "OPENAI_MAX_TOKENS": "500",
                "OPENAI_TEMPERATURE": "0.7",
            },
            {
                "OPENAI_API_KEY": "sk-another123456789",
                "OPENAI_MODEL": "gpt-4",
                "OPENAI_MAX_TOKENS": "1000",
                "OPENAI_TEMPERATURE": "0.3",
            },
        ],
        ids=["gpt_4o_mini_config", "gpt_4_config"],
    )
    def test_langchain_client_dependency_configuration_validation(self, config: dict[str, str]) -> None:
        """Test LangChain client dependency validates configuration properly."""
        # Clear cache before each test iteration to avoid stale cached values
        get_langchain_client.cache_clear()
        get_config.cache_clear()

        with patch.dict("os.environ", config):
            client = get_langchain_client()

            assert client.config.openai_api_key == config["OPENAI_API_KEY"]
            assert client.config.openai_model == config["OPENAI_MODEL"]
            assert client.config.openai_max_tokens == int(config["OPENAI_MAX_TOKENS"])
            assert client.config.openai_temperature == float(config["OPENAI_TEMPERATURE"])

    def test_langchain_client_components_initialization(self) -> None:
        """Test all LangChain client components are properly initialized."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test123456789"}):
            client = get_langchain_client()

            # Verify PromptManager is initialized
            assert client.prompt_manager is not None
            assert hasattr(client.prompt_manager, "render_system_prompt")
            assert hasattr(client.prompt_manager, "render_tutoring_prompt")
            assert hasattr(client.prompt_manager, "render_start_message")

            # Verify CorrectionParser is initialized
            assert client.correction_parser is not None
            assert hasattr(client.correction_parser, "parse_response")

    @pytest.mark.asyncio
    async def test_dependency_injection_in_endpoint_context(self) -> None:
        """Test dependency injection works correctly in FastAPI endpoint context."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from tutor_ai.dependencies import LangChainDep

        # Create test app with dependency
        app = FastAPI()

        @app.get("/test-dependency")
        async def test_endpoint(client: LangChainDep) -> dict[str, bool | str]:
            return {
                "client_type": type(client).__name__,
                "has_config": client.config is not None,
                "has_prompt_manager": client.prompt_manager is not None,
                "has_correction_parser": client.correction_parser is not None,
            }

        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test123456789"}):
            test_client = TestClient(app)
            response = test_client.get("/test-dependency")

            assert response.status_code == 200
            data = response.json()

            assert data["client_type"] == "LangChainClient"
            assert data["has_config"] is True
            assert data["has_prompt_manager"] is True
            assert data["has_correction_parser"] is True


class TestDependencyInjectionErrorHandling:
    """Test error handling in dependency injection system."""

    @pytest.mark.parametrize(
        "invalid_key",
        [
            "invalid-key",  # Wrong prefix
            "sk-",  # Too short
            "",  # Empty
            "sk-123",  # Too short
        ],
        ids=["wrong_prefix", "too_short_sk", "empty_key", "short_sk123"],
    )
    def test_get_langchain_client_with_invalid_api_key_format(self, invalid_key: str) -> None:
        """Test get_langchain_client handles invalid API key format."""
        # Clear cache before each test iteration
        get_langchain_client.cache_clear()
        get_config.cache_clear()

        # Use complete environment to prevent .env loading issues
        test_env = {
            "OPENAI_API_KEY": invalid_key,
            "SUPPORTED_LANGUAGES": '["EN","UA","PL","DE"]',  # Valid languages
        }

        with (
            patch.dict("os.environ", test_env, clear=True),
            patch("tutor_ai.dependencies.get_config") as mock_get_config,
        ):
            from tutor_ai.config import AppConfig

            mock_get_config.side_effect = lambda: AppConfig(_env_file=None)

            with pytest.raises(ValueError):
                get_langchain_client()

    @pytest.mark.parametrize(
        "invalid_temperature", ["-0.1", "2.1", "not-a-number", ""], ids=["negative", "too_high", "not_number", "empty"]
    )
    def test_get_langchain_client_with_invalid_temperature(self, invalid_temperature: str) -> None:
        """Test get_langchain_client handles invalid temperature values."""
        with (
            patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test123456789", "OPENAI_TEMPERATURE": invalid_temperature}),
            pytest.raises(ValueError),
        ):
            get_langchain_client()

    @pytest.mark.parametrize(
        "invalid_tokens", ["-1", "0", "not-a-number", ""], ids=["negative", "zero", "not_number", "empty"]
    )
    def test_get_langchain_client_with_invalid_max_tokens(self, invalid_tokens: str) -> None:
        """Test get_langchain_client handles invalid max_tokens values."""
        with (
            patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test123456789", "OPENAI_MAX_TOKENS": invalid_tokens}),
            pytest.raises(ValueError),
        ):
            get_langchain_client()

    def test_dependency_caching_survives_config_changes(self) -> None:
        """Test dependency caching behavior when configuration changes."""
        # Initial configuration
        config1 = {"OPENAI_API_KEY": "sk-first123456789"}
        with patch.dict("os.environ", config1):
            client1 = get_langchain_client()

        # Change configuration
        config2 = {"OPENAI_API_KEY": "sk-second123456789"}
        with patch.dict("os.environ", config2):
            client2 = get_langchain_client()

        # Due to caching, should still be the same instance
        assert client1 is client2

        # But config should reflect the cached version
        assert client1.config.openai_api_key == "sk-first123456789"


class TestDependencyPerformance:
    """Test performance characteristics of dependency injection."""

    def test_langchain_client_initialization_performance(self) -> None:
        """Test LangChain client initialization is reasonably fast."""
        import time

        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test123456789"}):
            start_time = time.time()

            # Initialize client
            client = get_langchain_client()

            end_time = time.time()
            initialization_time = end_time - start_time

            # Should initialize quickly (under 1 second)
            assert initialization_time < 1.0
            assert client is not None

    def test_cached_client_access_performance(self) -> None:
        """Test cached client access is very fast."""
        import time

        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test123456789"}):
            # First call - initialization
            get_langchain_client()

            # Measure cached access
            start_time = time.time()

            for _ in range(100):
                client = get_langchain_client()

            end_time = time.time()
            total_time = end_time - start_time

            # 100 cached accesses should be very fast (under 0.01 seconds)
            assert total_time < 0.01
            assert client is not None


class TestDependencyMocking:
    """Test mocking capabilities for dependency injection in tests."""

    @pytest.mark.asyncio
    async def test_mock_langchain_client_dependency(self) -> None:
        """Test ability to mock LangChain client dependency for testing."""
        import uuid

        from tutor_ai.chat.schemas import ChatRequest, ChatResponse
        from tutor_ai.enums import Language, Level

        # Create mock client
        mock_client = MagicMock(spec=LangChainClient)
        mock_response = ChatResponse(
            ai_response="Mock response",
            next_phrase="Mock next phrase",
            corrections=[],
            session_id=str(uuid.uuid4()),
            tokens_used=50,
        )
        mock_client.process_chat.return_value = mock_response

        # Test that mock can be used in place of real client
        request = ChatRequest(message="test", language=Language.EN, level=Level.B2, session_id=str(uuid.uuid4()))

        result = await mock_client.process_chat(request)

        assert result == mock_response
        mock_client.process_chat.assert_called_once_with(request)

    def test_dependency_override_capability(self) -> None:
        """Test that dependencies can be overridden for testing."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from tutor_ai.dependencies import LangChainDep

        app = FastAPI()

        @app.get("/test-override")
        async def test_endpoint(client: LangChainDep) -> dict[str, str]:
            return {"client_type": type(client).__name__}

        # Mock client for testing
        mock_client = MagicMock(spec=LangChainClient)

        # Override dependency
        app.dependency_overrides[get_langchain_client] = lambda: mock_client

        test_client = TestClient(app)
        response = test_client.get("/test-override")

        assert response.status_code == 200
        data = response.json()
        assert data["client_type"] == "MagicMock"

        # Clean up
        app.dependency_overrides.clear()
