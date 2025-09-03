"""Pytest configuration and shared fixtures for backend tests."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

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
