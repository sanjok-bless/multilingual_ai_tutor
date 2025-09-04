"""Tests for shared response schemas."""

import time

import pytest
from pydantic import ValidationError

from backend.schemas import ErrorResponse, HealthResponse


class TestErrorResponse:
    """Test ErrorResponse model validation and edge cases."""

    def test_valid_error_response_creation(self) -> None:
        """Test valid error response model creation."""
        timestamp = int(time.time())
        error = ErrorResponse(detail="Invalid request format", error_code="INVALID_FORMAT", timestamp=timestamp)

        assert error.detail == "Invalid request format"
        assert error.error_code == "INVALID_FORMAT"
        assert error.timestamp == timestamp

    def test_error_response_requires_all_fields(self) -> None:
        """Test error response requires all fields."""
        with pytest.raises(ValidationError):
            ErrorResponse(
                detail="Error message",
                # Missing error_code and timestamp
            )

        with pytest.raises(ValidationError):
            ErrorResponse(
                detail="Error message",
                error_code="ERROR_CODE",
                # Missing timestamp
            )

    def test_error_response_validates_field_types(self) -> None:
        """Test error response validates field types."""
        timestamp = int(time.time())

        # Valid types should work
        error = ErrorResponse(detail="Test error", error_code="TEST_ERROR", timestamp=timestamp)
        assert isinstance(error.detail, str)
        assert isinstance(error.error_code, str)
        assert isinstance(error.timestamp, int)

        # Invalid timestamp type should fail
        with pytest.raises(ValidationError):
            ErrorResponse(
                detail="Test error",
                error_code="TEST_ERROR",
                timestamp="not-an-integer",  # Should be int
            )

    def test_error_response_with_empty_strings(self) -> None:
        """Test error response behavior with empty strings."""
        timestamp = int(time.time())

        # Empty strings should be allowed (no min_length constraint)
        error = ErrorResponse(detail="", error_code="", timestamp=timestamp)
        assert error.detail == ""
        assert error.error_code == ""


class TestHealthResponse:
    """Test HealthResponse model validation and edge cases."""

    def test_valid_health_response_creation(self) -> None:
        """Test valid health response model creation."""
        timestamp = int(time.time())
        health = HealthResponse(
            status="healthy", message="Service is running normally", timestamp=timestamp, version="1.0.0"
        )

        assert health.status == "healthy"
        assert health.message == "Service is running normally"
        assert health.timestamp == timestamp
        assert health.version == "1.0.0"

    def test_health_response_with_default_version(self) -> None:
        """Test health response uses default version when not provided."""
        timestamp = int(time.time())
        health = HealthResponse(
            status="healthy",
            message="Service running",
            timestamp=timestamp,
            # version not provided - should use default
        )

        assert health.version == "0.1.0"  # Default from model definition

    def test_health_response_requires_mandatory_fields(self) -> None:
        """Test health response requires mandatory fields."""
        with pytest.raises(ValidationError):
            HealthResponse(
                status="healthy",
                # Missing message and timestamp
            )

        with pytest.raises(ValidationError):
            HealthResponse(
                message="Service running",
                timestamp=int(time.time()),
                # Missing status
            )

    def test_health_response_validates_field_types(self) -> None:
        """Test health response validates field types."""
        timestamp = int(time.time())

        # Valid types should work
        health = HealthResponse(status="healthy", message="Service running", timestamp=timestamp, version="1.0.0")
        assert isinstance(health.status, str)
        assert isinstance(health.message, str)
        assert isinstance(health.timestamp, int)
        assert isinstance(health.version, str)

        # Invalid timestamp type should fail
        with pytest.raises(ValidationError):
            HealthResponse(
                status="healthy",
                message="Service running",
                timestamp="not-an-integer",  # Should be int
                version="1.0.0",
            )

    def test_health_response_with_empty_strings(self) -> None:
        """Test health response behavior with empty strings."""
        timestamp = int(time.time())

        # Empty strings should be allowed (no min_length constraint)
        health = HealthResponse(status="", message="", timestamp=timestamp, version="")
        assert health.status == ""
        assert health.message == ""
        assert health.version == ""

    def test_health_response_common_status_values(self) -> None:
        """Test health response with common status values."""
        timestamp = int(time.time())

        # Test various common status values
        statuses = ["healthy", "unhealthy", "degraded", "unknown", "starting", "stopping"]
        for status in statuses:
            health = HealthResponse(status=status, message=f"Service is {status}", timestamp=timestamp)
            assert health.status == status
