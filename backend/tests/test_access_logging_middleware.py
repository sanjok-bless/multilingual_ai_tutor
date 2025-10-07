"""Tests for access logging middleware."""

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.middleware.access_logging import AccessLoggingMiddleware

# =============================================================================
# Test-specific fixtures - AccessLoggingMiddleware requires custom app setup
# =============================================================================


@pytest.fixture
def access_logging_app() -> FastAPI:
    """Create test FastAPI application with access logging middleware."""
    test_app = FastAPI()
    test_app.add_middleware(AccessLoggingMiddleware)

    @test_app.get("/test")
    async def test_endpoint() -> dict[str, str]:
        return {"message": "test"}

    @test_app.get("/error", response_model=None)
    async def error_endpoint() -> None:
        raise ValueError("test error")

    return test_app


@pytest.fixture
def access_logging_client(access_logging_app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(access_logging_app)


def test_middleware_logs_successful_request(access_logging_client: TestClient) -> None:
    """Test that middleware logs successful HTTP requests with correct structure."""
    with patch("backend.middleware.access_logging.logger") as mock_logger:
        response = access_logging_client.get("/test")

        assert response.status_code == 200
        mock_logger.info.assert_called_once()

        call_args = mock_logger.info.call_args
        assert call_args[0][0] == "HTTP request"
        assert call_args[1]["method"] == "GET"
        assert call_args[1]["path"] == "/test"
        assert call_args[1]["code"] == 200
        assert "ms" in call_args[1]
        assert isinstance(call_args[1]["ms"], float)
        assert call_args[1]["ms"] >= 0


def test_middleware_logs_request_with_client_ip(access_logging_client: TestClient) -> None:
    """Test that middleware captures client IP address."""
    with patch("backend.middleware.access_logging.logger") as mock_logger:
        response = access_logging_client.get("/test")

        assert response.status_code == 200
        call_args = mock_logger.info.call_args
        assert "ip" in call_args[1]
        assert call_args[1]["ip"] == "testclient"


def test_middleware_calculates_duration(access_logging_client: TestClient) -> None:
    """Test that middleware calculates request duration in milliseconds."""
    with patch("backend.middleware.access_logging.logger") as mock_logger:
        response = access_logging_client.get("/test")

        assert response.status_code == 200
        call_args = mock_logger.info.call_args
        # Verify duration is present, positive, and reasonable (< 1000ms for test)
        assert "ms" in call_args[1]
        assert isinstance(call_args[1]["ms"], float)
        assert 0 <= call_args[1]["ms"] < 1000


def test_middleware_logs_different_status_codes(access_logging_client: TestClient) -> None:
    """Test that middleware correctly logs different HTTP status codes."""
    with patch("backend.middleware.access_logging.logger") as mock_logger:
        # Test 404
        response = access_logging_client.get("/nonexistent")
        assert response.status_code == 404
        call_args = mock_logger.info.call_args
        assert call_args[1]["code"] == 404
        assert call_args[1]["path"] == "/nonexistent"


def test_middleware_returns_response_unchanged(access_logging_client: TestClient) -> None:
    """Test that middleware passes through response without modification."""
    response = access_logging_client.get("/test")

    assert response.status_code == 200
    assert response.json() == {"message": "test"}


def test_middleware_logs_different_http_methods(access_logging_client: TestClient) -> None:
    """Test that middleware logs different HTTP methods correctly."""

    @access_logging_client.app.post("/test-post")
    async def test_post() -> dict[str, str]:
        return {"method": "POST"}

    with patch("backend.middleware.access_logging.logger") as mock_logger:
        # Test POST
        response = access_logging_client.post("/test-post")
        assert response.status_code == 200
        call_args = mock_logger.info.call_args
        assert call_args[1]["method"] == "POST"
        assert call_args[1]["path"] == "/test-post"
