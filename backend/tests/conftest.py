"""Pytest configuration and shared fixtures for backend tests."""

from collections.abc import Callable
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from openai.types.chat import ChatCompletion

from backend.config import AppConfig
from backend.dependencies import get_config
from backend.main import create_app


@pytest.fixture
def mock_config() -> AppConfig:
    """Create a mock configuration for testing."""
    import os
    from unittest.mock import patch

    test_env = {
        "ENVIRONMENT": "ci",
        "OPENAI_API_KEY": "sk-test-key-for-testing",
        "OPENAI_MODEL": "gpt-4o-mini",
        "OPENAI_MAX_TOKENS": "500",
        "OPENAI_TEMPERATURE": "0.7",
        "SUPPORTED_LANGUAGES": '["english","ukrainian","polish","german"]',  # JSON format
        "CORS_ORIGINS": '["http://localhost:8080"]',  # JSON format
    }

    # Clear any existing environment variables that might interfere

    with patch.dict(os.environ, test_env, clear=False):
        # Use _env_file=None to prevent .env file loading during tests
        return AppConfig(_env_file=None)


@pytest.fixture
def app(mock_config: AppConfig) -> FastAPI:
    """Create FastAPI app with mocked configuration."""
    # We need to override the dependency BEFORE creating the app
    # because create_app() calls get_config() during initialization
    from unittest.mock import patch

    # Mock the get_config function at the main.py import location
    with patch("backend.main.get_config", return_value=mock_config):
        test_app = create_app()

    # Also set the override for any future calls during the test
    test_app.dependency_overrides[get_config] = lambda: mock_config
    return test_app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


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
