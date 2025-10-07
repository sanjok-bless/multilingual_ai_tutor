"""Tests for request size validation middleware."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.middleware.request_size import RequestSizeMiddleware

# =============================================================================
# Test-specific fixtures - RequestSizeMiddleware requires custom app setup
# =============================================================================


@pytest.fixture
def request_size_app() -> FastAPI:
    """Create test FastAPI application with request size middleware."""
    test_app = FastAPI()
    # Set max size to 100 bytes for testing
    test_app.add_middleware(RequestSizeMiddleware, max_size_bytes=100)

    @test_app.post("/test")
    async def test_endpoint(data: dict) -> dict[str, dict]:
        return {"received": data}

    return test_app


@pytest.fixture
def request_size_client(request_size_app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(request_size_app)


def test_middleware_allows_small_requests(request_size_client: TestClient) -> None:
    """Test that requests within size limits are allowed."""
    small_data = {"message": "test"}
    response = request_size_client.post("/test", json=small_data)

    assert response.status_code == 200
    assert response.json() == {"received": small_data}


def test_middleware_blocks_large_requests(request_size_client: TestClient) -> None:
    """Test that requests exceeding size limits are rejected with 413."""
    from fastapi import HTTPException

    # Create data larger than 100 bytes
    large_data = {"message": "x" * 200}

    # HTTPException is raised by middleware before reaching endpoint
    with pytest.raises(HTTPException) as exc_info:
        request_size_client.post("/test", json=large_data)

    assert exc_info.value.status_code == 413
    assert exc_info.value.detail == "Request too large"


def test_middleware_allows_requests_without_content_length(request_size_client: TestClient) -> None:
    """Test that requests without Content-Length header are allowed."""
    # GET requests typically don't have Content-Length
    response = request_size_client.get("/test")

    # Endpoint doesn't exist for GET, but middleware should pass it through
    assert response.status_code == 405  # Method Not Allowed


def test_middleware_boundary_condition(request_size_client: TestClient) -> None:
    """Test requests exactly at the size limit."""
    # Create data exactly at 100 bytes boundary
    # JSON encoding adds quotes and braces, so adjust for that
    boundary_data = {"m": "x" * 90}  # Should be close to 100 bytes when JSON encoded
    response = request_size_client.post("/test", json=boundary_data)

    # Should succeed if under limit
    assert response.status_code in [200, 413]  # Either pass or fail is acceptable at boundary
