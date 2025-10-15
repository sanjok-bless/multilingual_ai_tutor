"""Shared response schemas used across multiple API endpoints."""

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error response format."""

    detail: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Machine-readable error code")
    timestamp: int = Field(..., description="Unix timestamp when error occurred")


class HealthResponse(BaseModel):
    """Health check response format."""

    status: str = Field(..., description="Service status")
    message: str = Field(..., description="Human-readable status message")
    timestamp: int = Field(..., description="Unix timestamp of health check")
    version: str = Field(default="0.1.0", description="Application version")


class ConfigResponse(BaseModel):
    """Configuration response with supported languages and context limits."""

    languages: list[str] = Field(..., description="List of supported language codes")
    context_chat_limit: int = Field(..., description="Maximum context messages for chat endpoint")
    context_start_limit: int = Field(..., description="Maximum context messages for start endpoint")
