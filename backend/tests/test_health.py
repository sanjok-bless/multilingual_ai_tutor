"""Tests for health endpoint."""

import time

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    """Test health endpoint returns success."""
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "message" in data


class TestHealthEndpointNegativePaths:
    """Test health endpoint negative scenarios and error handling."""

    def test_health_endpoint_invalid_http_methods(self, client: TestClient) -> None:
        """Test health endpoint rejects invalid HTTP methods."""
        # POST should not be allowed on health endpoint
        response = client.post("/api/v1/health")
        assert response.status_code == 405  # Method Not Allowed

        # PUT should not be allowed
        response = client.put("/api/v1/health")
        assert response.status_code == 405

        # DELETE should not be allowed
        response = client.delete("/api/v1/health")
        assert response.status_code == 405

        # PATCH should not be allowed
        response = client.patch("/api/v1/health")
        assert response.status_code == 405

    def test_health_endpoint_with_request_body(self, client: TestClient) -> None:
        """Test health endpoint ignores request body on GET."""
        # GET with JSON body should still work (body should be ignored)
        response = client.request("GET", "/api/v1/health", json={"some": "data"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_endpoint_with_query_parameters(self, client: TestClient) -> None:
        """Test health endpoint ignores query parameters."""
        response = client.get("/api/v1/health?detailed=true&format=json")
        assert response.status_code == 200
        data = response.json()
        # Should return standard health response regardless of query params
        assert data["status"] == "healthy"
        assert "message" in data

    def test_health_endpoint_response_structure(self, client: TestClient) -> None:
        """Test health endpoint response structure matches HealthResponse schema."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()

        # Required fields must be present
        assert "status" in data
        assert "message" in data
        assert "timestamp" in data

        # Optional fields
        assert "version" in data

        # Field type validation
        assert isinstance(data["status"], str)
        assert isinstance(data["message"], str)
        assert isinstance(data["timestamp"], int)
        assert isinstance(data["version"], str)

        # Status should be reasonable value
        assert data["status"] == "healthy"  # Current implementation returns "healthy"

        # Timestamp should be reasonable (within last minute)
        current_time = int(time.time())
        response_time = data["timestamp"]
        time_diff = abs(current_time - response_time)
        assert time_diff < 60  # Response timestamp should be within 1 minute of now

    def test_health_endpoint_with_invalid_accept_header(self, client: TestClient) -> None:
        """Test health endpoint with unsupported Accept header."""
        # Request XML format (not supported)
        response = client.get("/api/v1/health", headers={"Accept": "application/xml"})
        # FastAPI should still return JSON (default)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_health_endpoint_with_custom_headers(self, client: TestClient) -> None:
        """Test health endpoint with various custom headers."""
        custom_headers = {
            "User-Agent": "HealthChecker/1.0",
            "X-Request-ID": "test-123",
            "Authorization": "Bearer fake-token",
        }

        response = client.get("/api/v1/health", headers=custom_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_endpoint_with_malformed_path(self, client: TestClient) -> None:
        """Test requests to malformed health paths."""
        # Double slashes
        response = client.get("/api/v1//health")
        assert response.status_code == 404  # Not Found

        # Trailing slash (should work or redirect)
        response = client.get("/api/v1/health/")
        assert response.status_code in [200, 301, 307]  # OK or redirect

        # Case sensitivity
        response = client.get("/api/v1/HEALTH")
        assert response.status_code == 404  # FastAPI is case-sensitive
