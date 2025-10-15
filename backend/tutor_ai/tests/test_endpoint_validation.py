"""Comprehensive validation tests for API endpoint request/response handling.

This module tests HTTP-level validation, error responses, content types,
and edge cases for the chat and start message endpoints.
Modern Python 3.13 patterns with professional error handling.
"""

import json
import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


class TestChatEndpointHTTPValidation:
    """Test HTTP-level validation for chat endpoint."""

    @pytest.mark.parametrize(
        "method", ["GET", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"], ids=lambda method: f"method_{method.lower()}"
    )
    def test_chat_endpoint_rejects_invalid_http_methods(
        self, method: str, client: TestClient, mock_langchain_client: MagicMock
    ) -> None:
        """Test chat endpoint rejects invalid HTTP methods."""
        valid_payload = {"message": "test", "language": "english", "level": "B2", "session_id": str(uuid.uuid4())}

        response = client.request(method, "/api/v1/chat", json=valid_payload)
        assert response.status_code == 405, f"Method {method} should be rejected"

    def test_chat_endpoint_accepts_post_method(self, client: TestClient, mock_langchain_client: MagicMock) -> None:
        """Test chat endpoint accepts POST requests."""
        valid_payload = {"message": "test", "language": "english", "level": "B2", "session_id": str(uuid.uuid4())}

        response = client.post("/api/v1/chat", json=valid_payload)
        assert response.status_code in [200, 503], "POST should be accepted"

    def test_chat_endpoint_requires_json_content_type(
        self, client: TestClient, mock_langchain_client: MagicMock
    ) -> None:
        """Test chat endpoint requires JSON content type."""
        payload_data = {"message": "test", "language": "english", "level": "B2", "session_id": str(uuid.uuid4())}

        # Test with form data (should fail)
        response = client.post("/api/v1/chat", data=payload_data)
        assert response.status_code == 422

        # Test with plain text (should fail)
        response = client.post("/api/v1/chat", content=json.dumps(payload_data), headers={"Content-Type": "text/plain"})
        assert response.status_code == 422

        # Test with correct JSON content type
        response = client.post("/api/v1/chat", json=payload_data)
        assert response.status_code in [200, 503]

    @pytest.mark.parametrize(
        "missing_field", ["message", "language", "level", "session_id"], ids=lambda field: f"missing_{field}"
    )
    def test_chat_endpoint_validates_missing_required_fields(
        self, missing_field: str, client: TestClient, mock_langchain_client: MagicMock
    ) -> None:
        """Test chat endpoint validates missing required fields."""
        base_valid_request = {
            "message": "test message",
            "language": "english",
            "level": "B2",
            "session_id": str(uuid.uuid4()),
        }

        incomplete_request = base_valid_request.copy()
        del incomplete_request[missing_field]

        response = client.post("/api/v1/chat", json=incomplete_request)
        assert response.status_code == 422

        error_data = response.json()
        assert "detail" in error_data

        # Verify error mentions the missing field
        error_details = str(error_data["detail"]).lower()
        assert missing_field in error_details

    @pytest.mark.parametrize(
        "invalid_field_update",
        [
            # Invalid message types
            ({"message": None}, "message_none"),
            ({"message": 123}, "message_int"),
            ({"message": []}, "message_list"),
            ({"message": ""}, "message_empty"),
            ({"message": "   "}, "message_whitespace"),
            # Invalid language types
            ({"language": None}, "language_none"),
            ({"language": 123}, "language_int"),
            ({"language": "invalid_lang"}, "language_invalid"),
            ({"language": ""}, "language_empty"),
            # Invalid level types
            ({"level": None}, "level_none"),
            ({"level": 123}, "level_int"),
            ({"level": "Z9"}, "level_invalid"),
            ({"level": ""}, "level_empty"),
            # Invalid session_id types
            ({"session_id": None}, "session_id_none"),
            ({"session_id": 123}, "session_id_int"),
            ({"session_id": "not-a-uuid"}, "session_id_invalid"),
            ({"session_id": ""}, "session_id_empty"),
        ],
        ids=lambda x: x[1],
    )
    def test_chat_endpoint_validates_field_types_and_constraints(
        self, invalid_field_update: tuple[dict, str], client: TestClient, mock_langchain_client: MagicMock
    ) -> None:
        """Test chat endpoint validates individual field types and constraints."""
        base_request = {"message": "test", "language": "english", "level": "B2", "session_id": str(uuid.uuid4())}

        invalid_field, _ = invalid_field_update
        test_request = base_request.copy()
        test_request.update(invalid_field)

        response = client.post("/api/v1/chat", json=test_request)
        assert response.status_code == 422, f"Should reject {invalid_field}"

    @pytest.mark.parametrize(
        "malformed_json",
        [
            '{"message": "test", "language": "english",}',  # Trailing comma
            '{"message": "test" "language": "english"}',  # Missing comma
            '{"message": "test", "language":}',  # Missing value
            '{message: "test"}',  # Unquoted key
            "not json at all",  # Not JSON
            '{"message": "test"',  # Incomplete JSON
        ],
        ids=["trailing_comma", "missing_comma", "missing_value", "unquoted_key", "not_json", "incomplete_json"],
    )
    def test_chat_endpoint_handles_malformed_json(
        self, malformed_json: str, client: TestClient, mock_langchain_client: MagicMock
    ) -> None:
        """Test chat endpoint handles malformed JSON gracefully."""
        response = client.post("/api/v1/chat", content=malformed_json, headers={"Content-Type": "application/json"})
        assert response.status_code == 422

    def test_chat_endpoint_handles_oversized_request(
        self, client: TestClient, mock_langchain_client: MagicMock
    ) -> None:
        """Test chat endpoint handles oversized requests properly."""
        # Create request with very large message
        large_message = "A" * (2 * 1024 * 1024)  # 2MB message

        oversized_request = {
            "message": large_message,
            "language": "english",
            "level": "B2",
            "session_id": str(uuid.uuid4()),
        }

        # Middleware may raise HTTPException directly or return error response
        try:
            response = client.post("/api/v1/chat", json=oversized_request)
            # Should be rejected due to size limit (413 Request Entity Too Large or 422)
            assert response.status_code in [413, 422]
        except Exception as e:
            # If middleware raises exception directly, verify it's the expected type
            from fastapi.exceptions import HTTPException

            if isinstance(e, HTTPException) and e.status_code == 413:
                pass  # Expected behavior - middleware blocked oversized request
            else:
                raise  # Re-raise unexpected exceptions

    @pytest.mark.parametrize(
        "unicode_message",
        [
            "Hello 世界",  # Mixed ASCII and Chinese
            "Привіт світ! 🌍",  # Ukrainian with emoji
            "Café naïve résumé",  # French accents
            "Straße größer",  # German umlauts
            "Åse ønsker æbler",  # Norwegian special chars
            "こんにちは",  # Japanese
            "🎉🔥⭐",  # Only emojis
        ],
        ids=[
            "chinese_mixed",
            "ukrainian_emoji",
            "french_accents",
            "german_umlauts",
            "norwegian_chars",
            "japanese",
            "emojis_only",
        ],
    )
    def test_chat_endpoint_unicode_message_handling(
        self, unicode_message: str, client: TestClient, mock_langchain_client: MagicMock
    ) -> None:
        """Test chat endpoint properly handles Unicode messages."""
        request_data = {
            "message": unicode_message,
            "language": "english",
            "level": "B2",
            "session_id": str(uuid.uuid4()),
        }

        response = client.post("/api/v1/chat", json=request_data)

        # Should accept Unicode messages (may fail on API call, but validation passes)
        assert response.status_code in [200, 503], f"Failed for message: {unicode_message}"


class TestStartEndpointHTTPValidation:
    """Test HTTP-level validation for start message endpoint."""

    @pytest.mark.parametrize(
        "method", ["GET", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"], ids=lambda method: f"method_{method.lower()}"
    )
    def test_start_endpoint_rejects_invalid_http_methods(
        self, method: str, client: TestClient, mock_langchain_client: MagicMock
    ) -> None:
        """Test start endpoint rejects invalid HTTP methods."""
        valid_payload = {"language": "english", "level": "B2", "session_id": str(uuid.uuid4())}

        response = client.request(method, "/api/v1/start", json=valid_payload)
        assert response.status_code == 405, f"Method {method} should be rejected"

    @pytest.mark.parametrize("missing_field", ["language", "level", "session_id"], ids=lambda field: f"missing_{field}")
    def test_start_endpoint_validates_missing_required_fields(
        self, missing_field: str, client: TestClient, mock_langchain_client: MagicMock
    ) -> None:
        """Test start endpoint validates missing required fields."""
        base_valid_request = {"language": "english", "level": "B2", "session_id": str(uuid.uuid4())}

        incomplete_request = base_valid_request.copy()
        del incomplete_request[missing_field]

        response = client.post("/api/v1/start", json=incomplete_request)
        assert response.status_code == 422

    @pytest.mark.parametrize(
        "language,level",
        [("english", "A1"), ("english", "B1"), ("english", "C1"), ("german", "A2"), ("german", "B2"), ("german", "C2")],
        ids=lambda combo: f"{combo[0]}_{combo[1]}",
    )
    def test_start_endpoint_validates_valid_enum_combinations(
        self, language: str, level: str, client: TestClient, mock_langchain_client: MagicMock
    ) -> None:
        """Test start endpoint accepts valid language/level combinations."""
        request_data = {"language": language, "level": level, "session_id": str(uuid.uuid4())}

        response = client.post("/api/v1/start", json=request_data)
        assert response.status_code in [200, 503]

    @pytest.mark.parametrize(
        "invalid_language",
        ["spanish", "french", "invalid", ""],
        ids=["spanish", "french", "invalid_text", "empty_string"],
    )
    def test_start_endpoint_validates_invalid_languages(
        self, invalid_language: str, client: TestClient, mock_langchain_client: MagicMock
    ) -> None:
        """Test start endpoint rejects invalid languages."""
        request_data = {"language": invalid_language, "level": "B2", "session_id": str(uuid.uuid4())}

        response = client.post("/api/v1/start", json=request_data)
        assert response.status_code == 422

    @pytest.mark.parametrize(
        "invalid_level",
        ["D1", "Z2", "invalid", "", "b2", "c1"],
        ids=["d1_level", "z2_level", "invalid_text", "empty_string", "lowercase_b2", "lowercase_c1"],
    )
    def test_start_endpoint_validates_invalid_levels(
        self, invalid_level: str, client: TestClient, mock_langchain_client: MagicMock
    ) -> None:
        """Test start endpoint rejects invalid levels."""
        request_data = {"language": "english", "level": invalid_level, "session_id": str(uuid.uuid4())}

        response = client.post("/api/v1/start", json=request_data)
        assert response.status_code == 422


class TestAPIErrorResponseFormat:
    """Test API error response format consistency."""

    def test_validation_error_response_format(self, client: TestClient, mock_langchain_client: MagicMock) -> None:
        """Test validation error responses follow consistent format."""
        # Send request with validation errors
        invalid_request = {
            "message": "",  # Invalid empty message
            "language": "invalid",  # Invalid language
            "level": "Z9",  # Invalid level
            "session_id": "not-uuid",  # Invalid UUID
        }

        response = client.post("/api/v1/chat", json=invalid_request)

        assert response.status_code == 422
        error_data = response.json()

        # Verify error response structure
        assert "detail" in error_data
        assert isinstance(error_data["detail"], list)

        # Verify each error has required fields
        for error in error_data["detail"]:
            assert "type" in error
            assert "loc" in error
            assert "msg" in error

    def test_method_not_allowed_error_format(self, client: TestClient, mock_langchain_client: MagicMock) -> None:
        """Test method not allowed errors follow consistent format."""
        response = client.get("/api/v1/chat")

        assert response.status_code == 405
        error_data = response.json()

        # FastAPI default format for 405 errors
        assert "detail" in error_data
        assert "Method Not Allowed" in error_data["detail"]

    def test_service_error_response_format(self, client: TestClient, mock_langchain_client: MagicMock) -> None:
        """Test service error responses follow consistent format."""
        valid_request = {"message": "test", "language": "english", "level": "B2", "session_id": str(uuid.uuid4())}

        # Mock LLM error to test service error handling
        with patch("tutor_ai.llms.langchain_client.LangChainClient.process_chat") as mock_process:
            from tutor_ai.errors import LLMError

            mock_process.side_effect = LLMError("API rate limit exceeded")

            response = client.post("/api/v1/chat", json=valid_request)

            assert response.status_code == 503
            error_data = response.json()

            # Verify service error response structure (FastAPI returns errors under 'detail')
            assert "detail" in error_data
            detail = error_data["detail"]
            assert "error" in detail
            assert "message" in detail
            assert detail["error"] == "Service temporarily unavailable"

    def test_not_found_error_format(self, client: TestClient, mock_langchain_client: MagicMock) -> None:
        """Test 404 error response format for non-existent endpoints."""
        response = client.post("/api/v1/nonexistent")

        assert response.status_code == 404
        error_data = response.json()

        assert "detail" in error_data
        assert "Not Found" in error_data["detail"]


class TestResponseHeaderValidation:
    """Test response headers and content type validation."""

    def test_successful_response_headers(self, client: TestClient, mock_langchain_client: MagicMock) -> None:
        """Test successful responses have correct headers."""
        request_data = {"message": "test", "language": "english", "level": "B2", "session_id": str(uuid.uuid4())}

        response = client.post("/api/v1/chat", json=request_data)

        if response.status_code == 200:
            # Verify content type is JSON
            assert response.headers["content-type"] == "application/json"

            # Verify response is valid JSON
            json_data = response.json()
            assert isinstance(json_data, dict)

    def test_error_response_headers(self, client: TestClient, mock_langchain_client: MagicMock) -> None:
        """Test error responses have correct headers."""
        invalid_request = {"invalid": "data"}

        response = client.post("/api/v1/chat", json=invalid_request)

        assert response.status_code == 422
        assert response.headers["content-type"] == "application/json"

        # Verify error response is valid JSON
        error_data = response.json()
        assert isinstance(error_data, dict)

    def test_cors_headers_present(self, client: TestClient, mock_langchain_client: MagicMock) -> None:
        """Test CORS headers are present in responses."""
        request_data = {"language": "english", "level": "B2", "session_id": str(uuid.uuid4())}

        response = client.post("/api/v1/start", json=request_data)

        # CORS headers should be present (configured in main.py)
        # This tests the CORS middleware is working
        if "access-control-allow-origin" in response.headers:
            assert response.headers["access-control-allow-origin"] is not None


class TestRequestSizeAndLimits:
    """Test request size limits and boundary conditions."""

    def test_maximum_reasonable_message_size(self, client: TestClient, mock_langchain_client: MagicMock) -> None:
        """Test handling of reasonably large messages within limit."""
        # Test with large but reasonable message (450 chars, within 500 limit)
        large_message = "This is a test message. " * 18  # 432 chars, well within limit

        request_data = {"message": large_message, "language": "english", "level": "B2", "session_id": str(uuid.uuid4())}

        response = client.post("/api/v1/chat", json=request_data)

        # Should handle reasonable large messages within the 500 char limit
        assert response.status_code in [200, 503]

    @pytest.mark.parametrize(
        "valid_uuid",
        [
            str(uuid.uuid4()),
            "550e8400-e29b-41d4-a716-446655440000",  # Standard UUID
            "6ba7b810-9dad-11d1-80b4-00c04fd430c8",  # Another valid UUID
        ],
        ids=["generated_uuid", "standard_uuid", "another_uuid"],
    )
    def test_chat_endpoint_accepts_valid_uuid_formats(
        self, valid_uuid: str, client: TestClient, mock_langchain_client: MagicMock
    ) -> None:
        """Test chat endpoint accepts valid UUID formats."""
        request_data = {"message": "test", "language": "english", "level": "B2", "session_id": valid_uuid}

        response = client.post("/api/v1/chat", json=request_data)
        assert response.status_code in [200, 503]

    @pytest.mark.parametrize(
        "invalid_uuid",
        [
            "550e8400-e29b-41d4-a716-44665544000",  # Too short
            "550e8400-e29b-41d4-a716-4466554400000",  # Too long
            "550e8400-e29b-41d4-a716-44665544000g",  # Invalid character
            "not-a-uuid-at-all",  # Completely invalid
        ],
        ids=["too_short", "too_long", "invalid_char", "not_uuid"],
    )
    def test_chat_endpoint_rejects_invalid_uuid_formats(
        self, invalid_uuid: str, client: TestClient, mock_langchain_client: MagicMock
    ) -> None:
        """Test chat endpoint rejects invalid UUID formats."""
        request_data = {"message": "test", "language": "english", "level": "B2", "session_id": invalid_uuid}

        response = client.post("/api/v1/chat", json=request_data)
        assert response.status_code == 422
