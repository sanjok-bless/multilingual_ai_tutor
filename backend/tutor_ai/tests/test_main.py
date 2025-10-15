"""Test the main FastAPI application."""

import os
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_create_app() -> None:
    """Test that the FastAPI app is created successfully."""
    from tutor_ai.main import create_app

    # Mock environment with required API key
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key-for-testing"}):
        app = create_app()
        assert app is not None
        assert app.title == "Multilingual AI Tutor"
        assert app.version == "0.1.0"


class TestDocsEndpointsAvailability:
    """Test documentation endpoints availability across environments."""

    @pytest.fixture(params=["dev", "prod", "ci"])
    def environment(self, request: pytest.FixtureRequest) -> str:
        """Parametrized fixture providing all three environments."""
        return request.param

    @pytest.fixture
    def app_for_environment(self, environment: str) -> FastAPI:
        """Create FastAPI app configured for specific environment."""
        from tutor_ai.dependencies import get_config
        from tutor_ai.main import create_app

        env_vars = {"OPENAI_API_KEY": "sk-test-key-for-testing", "ENVIRONMENT": environment}

        # Clear the lru_cache to ensure fresh config loading
        get_config.cache_clear()

        with patch.dict(os.environ, env_vars):
            app = create_app()

        # Clear cache after creating app to ensure isolation
        get_config.cache_clear()
        return app

    @pytest.fixture
    def client_for_environment(self, app_for_environment: FastAPI) -> TestClient:
        """Create test client for environment-specific app."""
        return TestClient(app_for_environment)

    def test_docs_endpoint_availability_by_environment(
        self, environment: str, client_for_environment: TestClient
    ) -> None:
        """Test /docs endpoint availability based on environment."""
        response = client_for_environment.get("/docs")

        if environment == "dev":
            assert response.status_code == 200
            assert "swagger" in response.text.lower() or "openapi" in response.text.lower()
        else:  # prod or ci
            assert response.status_code == 404

    def test_redoc_endpoint_availability_by_environment(
        self, environment: str, client_for_environment: TestClient
    ) -> None:
        """Test /redoc endpoint availability based on environment."""
        response = client_for_environment.get("/redoc")

        if environment == "dev":
            assert response.status_code == 200
            assert "redoc" in response.text.lower()
        else:  # prod or ci
            assert response.status_code == 404

    def test_app_docs_url_configuration_by_environment(self, environment: str, app_for_environment: FastAPI) -> None:
        """Test FastAPI app docs_url configuration based on environment."""
        if environment == "dev":
            assert app_for_environment.docs_url == "/docs"
            assert app_for_environment.redoc_url == "/redoc"
        else:  # prod or ci
            assert app_for_environment.docs_url is None
            assert app_for_environment.redoc_url is None
