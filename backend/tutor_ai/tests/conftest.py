"""Pytest configuration and shared fixtures for backend tests."""

import uuid
from collections.abc import Callable, Generator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from openai.types.chat import ChatCompletion

from tutor_ai.config import AppConfig
from tutor_ai.dependencies import get_config
from tutor_ai.main import create_app

# =============================================================================
# SESSION-SCOPED FIXTURES
# =============================================================================


@pytest.fixture(scope="session")
def mock_config(setup_test_environment: Generator[None]) -> AppConfig:
    """Create a mock configuration for testing."""
    # Rely on setup_test_environment fixture for environment setup
    # Use _env_file=None to prevent .env file loading during tests
    return AppConfig(_env_file=None)


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment() -> Generator[None]:
    """Set up test environment variables for all tests to work with PyCharm and other test runners."""
    import os

    # Set up default test environment variables
    # These can be overridden by individual tests using patch.dict
    original_env = os.environ.copy()

    test_env = {
        "ENVIRONMENT": "ci",
        "OPENAI_API_KEY": "sk-test-key-for-testing",
        "OPENAI_MODEL": "gpt-4o-mini",
        "OPENAI_MAX_TOKENS": "500",
        "OPENAI_TEMPERATURE": "0.7",
        "SUPPORTED_LANGUAGES": '["english","ukrainian","polish","german"]',
        "CORS_ORIGINS": '["http://localhost:8080"]',
    }

    # Update environment with test values
    os.environ.update(test_env)

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# =============================================================================
# APP-LEVEL FIXTURES
# =============================================================================


@pytest.fixture
def app(mock_config: AppConfig) -> FastAPI:
    """Create FastAPI app with mocked configuration."""
    # The autouse fixture handles patching get_config globally
    test_app = create_app()

    # Set the dependency override for FastAPI's dependency injection system
    test_app.dependency_overrides[get_config] = lambda: mock_config
    return test_app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


# =============================================================================
# TEST DATA FIXTURES
# =============================================================================


@pytest.fixture
def valid_chat_request_data() -> dict[str, str]:
    """Valid chat request data for testing."""
    return {"message": "I have meeting tomorrow", "language": "english", "level": "B2", "session_id": str(uuid.uuid4())}


@pytest.fixture
def valid_start_request_data() -> dict[str, str]:
    """Valid start message request data for testing."""
    return {"language": "english", "level": "B2", "session_id": str(uuid.uuid4())}


# =============================================================================
# LLM FIXTURES
# =============================================================================


@pytest.fixture
def ai_response_loader() -> Callable[[str], str]:
    """Load AI response fixtures from files."""
    fixtures_dir = Path(__file__).parent / "fixtures" / "ai_responses"

    def _load(scenario: str) -> str:
        """Load AI response fixture by scenario name."""
        # Handle malformed responses in subdirectory
        if scenario.startswith("malformed_"):
            scenario_file = scenario[len("malformed_") :]  # Remove prefix
            fixture_path = fixtures_dir / "malformed_responses" / f"{scenario_file}.txt"
        else:
            fixture_path = fixtures_dir / f"{scenario}.txt"

        if not fixture_path.exists():
            raise FileNotFoundError(f"AI response fixture not found: {fixture_path}")

        return fixture_path.read_text(encoding="utf-8")

    return _load


@pytest.fixture
def mock_langchain_client(ai_response_loader: Callable[[str], str]) -> Generator[MagicMock]:
    """Mock LangChain ChatOpenAI client using existing file-based fixtures."""
    with patch("tutor_ai.llms.langchain_client.ChatOpenAI") as mock_openai:
        # Create async mock response that behaves like real LangChain response
        mock_response = AsyncMock()

        # Default to perfect message response from existing fixture files
        try:
            response_content = ai_response_loader("perfect_message")
        except FileNotFoundError:
            # Fallback if file doesn't exist
            response_content = "## 1. NEXT_PHRASE\nGreat!\n\n## 2. AI_RESPONSE\nPerfect!\n\n## 3. CORRECTIONS\n[]"

        mock_response.content = response_content
        mock_response.response_metadata = {"token_usage": {"total_tokens": 89}}

        # Configure mock to return the response
        mock_client_instance = AsyncMock()
        mock_client_instance.ainvoke.return_value = mock_response
        mock_openai.return_value = mock_client_instance

        # Store objects for dynamic configuration in tests
        mock_openai.mock_response = mock_response
        mock_openai.mock_client_instance = mock_client_instance
        mock_openai.ai_response_loader = ai_response_loader

        yield mock_openai


class MockHelper:
    """Helper class for configuring mock LangChain responses using file-based fixtures."""

    @staticmethod
    def configure_response(mock_openai: MagicMock, scenario: str, _unused_responses: dict = None) -> None:
        """Configure mock to return specific response from fixture files."""
        ai_response_loader = mock_openai.ai_response_loader

        try:
            response_content = ai_response_loader(scenario)
        except FileNotFoundError:
            # Map scenario names to existing fixture files (for legacy scenarios only)
            scenario_mapping = {
                "grammar_error": "grammar_error_single",
                "perfect_message": "perfect_message",
                "spelling_error": "spelling_error",
            }
            mapped_scenario = scenario_mapping.get(scenario, "perfect_message")
            try:
                response_content = ai_response_loader(mapped_scenario)
            except FileNotFoundError:
                # Final fallback
                response_content = "## 1. NEXT_PHRASE\nGreat!\n\n## 2. AI_RESPONSE\nPerfect!\n\n## 3. CORRECTIONS\n[]"

        mock_openai.mock_response.content = response_content

        # Set appropriate token count based on response type
        token_counts = {"grammar_error": 145, "perfect_message": 89, "spelling_error": 112}
        tokens = token_counts.get(scenario, 50)
        mock_openai.mock_response.response_metadata = {"token_usage": {"total_tokens": tokens}}

    @staticmethod
    def configure_error(mock_openai: MagicMock, error_type: type, error_message: str) -> None:
        """Configure mock to raise specific error type."""
        mock_openai.mock_client_instance.ainvoke.side_effect = error_type(error_message)

    @staticmethod
    def configure_malformed_response(mock_openai: MagicMock, malformed_content: str) -> None:
        """Configure mock to return malformed response for fallback testing."""
        mock_openai.mock_response.content = malformed_content
        mock_openai.mock_response.response_metadata = {"token_usage": {"total_tokens": 25}}


@pytest.fixture
def mock_helper() -> type:
    """Provide helper class for dynamic mock configuration using file-based fixtures."""
    return MockHelper


# =============================================================================
# MOCK FACTORIES
# =============================================================================


@pytest.fixture
def mock_openai_response() -> Callable[[str, int], ChatCompletion]:
    """Create mock OpenAI ChatCompletion responses."""

    def _create(content: str, tokens: int = 100) -> ChatCompletion:
        """Create a mock OpenAI ChatCompletion response."""
        mock_response = Mock(spec=ChatCompletion)

        # Mock the message structure
        mock_message = Mock()
        mock_message.content = content

        mock_choice = Mock()
        mock_choice.message = mock_message

        mock_response.choices = [mock_choice]

        # Mock usage information
        mock_usage = Mock()
        mock_usage.prompt_tokens = tokens // 2
        mock_usage.completion_tokens = tokens // 2
        mock_usage.total_tokens = tokens

        mock_response.usage = mock_usage

        return mock_response

    return _create


# =============================================================================
# UTILITY FIXTURES
# =============================================================================


@pytest.fixture(autouse=True)
def clear_dependency_caches() -> Generator[None]:
    """Automatically clear dependency injection caches between tests for isolation."""
    yield

    # Clear caches after each test to ensure isolation
    try:
        from tutor_ai.dependencies import get_config, get_langchain_client

        get_config.cache_clear()
        get_langchain_client.cache_clear()
    except ImportError:
        # Dependencies may not exist yet (TDD red phase)
        pass


# =============================================================================
# MIDDLEWARE FIXTURES
# =============================================================================


@pytest.fixture
def test_app_factory() -> Callable:
    """Factory for creating test FastAPI apps with custom middleware configurations.

    Example usage:
        def test_my_middleware(test_app_factory):
            app = test_app_factory(
                (MyMiddleware, {"config": "value"}),
                (OtherMiddleware, {})
            )
    """

    def _create(*middleware_configs: tuple) -> FastAPI:
        """Create FastAPI app with specified middleware.

        Args:
            *middleware_configs: Tuples of (middleware_class, kwargs_dict)

        Returns:
            Configured FastAPI application
        """
        test_app = FastAPI()
        for middleware_class, kwargs in middleware_configs:
            test_app.add_middleware(middleware_class, **kwargs)
        return test_app

    return _create
