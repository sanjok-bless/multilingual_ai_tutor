"""Pydantic schemas and data models for chat functionality."""

import uuid
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, field_validator

from backend.enums import ErrorType, Language, Level


def _validate_uuid_format(v: str) -> str:
    """Validate that string is a valid UUID format."""
    try:
        uuid.UUID(v)
    except ValueError as e:
        msg = "session_id must be a valid UUID format"
        raise ValueError(msg) from e
    return v


# Type alias for user message with validation constraints
UserMessage = Annotated[str, StringConstraints(min_length=1, max_length=500, strip_whitespace=True)]


class Correction(BaseModel):
    """Model for individual language corrections."""

    original: str = Field(..., min_length=1, description="Original incorrect text")
    corrected: str = Field(..., min_length=1, description="Corrected version of the text")
    explanation: list[str] = Field(..., description="Structured explanation as [category, description]")
    error_type: ErrorType = Field(..., description="Type of error being corrected")

    @field_validator("explanation")
    @classmethod
    def validate_explanation_length(cls, v: list[str]) -> list[str]:
        if len(v) != 2:
            msg = "Explanation must have exactly 2 elements: [category, description]"
            raise ValueError(msg)
        return v


class ChatRequest(BaseModel):
    """Model for incoming chat requests."""

    message: UserMessage = Field(..., description="User's message to be processed")
    language: Language = Field(..., description="Target language for correction")
    level: Level = Field(..., description="User's proficiency level")
    session_id: str = Field(..., description="UUID session identifier")
    context_messages: list[dict] = Field(default=[], description="Previous conversation messages for context")

    @field_validator("session_id")
    @classmethod
    def validate_session_id_format(cls, v: str) -> str:
        return _validate_uuid_format(v)


class ChatResponse(BaseModel):
    """Model for AI chat responses."""

    ai_response: str = Field(..., min_length=1, description="AI's natural explanation or positive feedback")
    next_phrase: str = Field(..., min_length=1, description="AI's conversational response/next phrase")
    corrections: list[Correction] = Field(default=[], description="List of corrections made")
    session_id: str = Field(..., description="UUID session identifier from request")
    tokens_used: int = Field(..., ge=0, description="Number of tokens consumed by the request")


class StartMessageRequest(BaseModel):
    """Model for start message generation requests."""

    language: Language = Field(..., description="Target language for the start message")
    level: Level = Field(..., description="User's proficiency level")
    session_id: str = Field(..., description="UUID session identifier")
    context_messages: list[dict] = Field(default=[], description="Previous conversation messages for context")

    @field_validator("session_id")
    @classmethod
    def validate_session_id_format(cls, v: str) -> str:
        return _validate_uuid_format(v)


class StartMessageResponse(BaseModel):
    """Model for start message generation responses."""

    message: str = Field(..., min_length=1, description="Generated start message from AI tutor")
    session_id: str = Field(..., description="UUID session identifier from request")
    tokens_used: int = Field(..., ge=0, description="Number of tokens consumed by the request")
