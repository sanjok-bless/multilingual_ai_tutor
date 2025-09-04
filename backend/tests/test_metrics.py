"""Tests for metrics endpoint."""

from fastapi.testclient import TestClient


def test_metrics_endpoint(client: TestClient) -> None:
    """Test metrics endpoint returns empty dict."""
    response = client.get("/api/v1/metrics")

    assert response.status_code == 200
    data = response.json()
    assert data == {}


class TestMetricsEndpointNegativePaths:
    """Test metrics endpoint negative scenarios and error handling."""

    def test_metrics_endpoint_invalid_http_methods(self, client: TestClient) -> None:
        """Test metrics endpoint rejects invalid HTTP methods."""
        # POST should not be allowed on metrics endpoint
        response = client.post("/api/v1/metrics")
        assert response.status_code == 405  # Method Not Allowed

        # PUT should not be allowed
        response = client.put("/api/v1/metrics")
        assert response.status_code == 405

        # DELETE should not be allowed
        response = client.delete("/api/v1/metrics")
        assert response.status_code == 405

        # PATCH should not be allowed
        response = client.patch("/api/v1/metrics")
        assert response.status_code == 405

    def test_metrics_endpoint_with_request_body(self, client: TestClient) -> None:
        """Test metrics endpoint ignores request body on GET."""
        # GET with JSON body should still work (body should be ignored)
        response = client.request("GET", "/api/v1/metrics", json={"filter": "errors", "limit": 100})
        assert response.status_code == 200
        data = response.json()
        assert data == {}  # Current implementation returns empty dict

    def test_metrics_endpoint_with_query_parameters(self, client: TestClient) -> None:
        """Test metrics endpoint ignores query parameters."""
        response = client.get("/api/v1/metrics?format=prometheus&detailed=true")
        assert response.status_code == 200
        data = response.json()
        # Should return empty dict regardless of query params
        assert data == {}

    def test_metrics_endpoint_response_format(self, client: TestClient) -> None:
        """Test metrics endpoint response format consistency."""
        response = client.get("/api/v1/metrics")
        assert response.status_code == 200

        # Should return JSON content type
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert isinstance(data, dict)
        # Current implementation returns empty dict
        assert data == {}

    def test_metrics_endpoint_with_accept_headers(self, client: TestClient) -> None:
        """Test metrics endpoint with different Accept headers."""
        # Test with application/json (default)
        response = client.get("/api/v1/metrics", headers={"Accept": "application/json"})
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        # Test with text/plain (common for Prometheus metrics)
        response = client.get("/api/v1/metrics", headers={"Accept": "text/plain"})
        # Should still return JSON (current implementation)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_metrics_endpoint_with_custom_headers(self, client: TestClient) -> None:
        """Test metrics endpoint with various custom headers."""
        custom_headers = {
            "User-Agent": "PrometheusCollector/2.0",
            "X-Monitoring-Service": "grafana",
            "Authorization": "Bearer metrics-token",
        }

        response = client.get("/api/v1/metrics", headers=custom_headers)
        assert response.status_code == 200
        data = response.json()
        assert data == {}

    def test_metrics_endpoint_with_malformed_path(self, client: TestClient) -> None:
        """Test requests to malformed metrics paths."""
        # Double slashes
        response = client.get("/api/v1//metrics")
        assert response.status_code == 404  # Not Found

        # Trailing slash (should work or redirect)
        response = client.get("/api/v1/metrics/")
        assert response.status_code in [200, 301, 307]  # OK or redirect

        # Case sensitivity
        response = client.get("/api/v1/METRICS")
        assert response.status_code == 404  # FastAPI is case-sensitive
