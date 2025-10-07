"""Configuration management with Pydantic Settings."""

import json
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.enums import Language

# Type aliases for better type safety
type Environment = Literal["dev", "prod", "ci"]


class AppConfig(BaseSettings):
    """App configuration."""

    # Application settings
    environment: Environment = Field(default="dev", description="Environment (dev/prod/ci)")
    cors_origins: list[str] = Field(default=["http://localhost:8080"], description="CORS allowed origins")
    cors_headers: list[str] = Field(
        default=["Content-Type", "Accept", "Origin", "X-Request-Time", "DNT", "Referer", "User-Agent"],
        description="CORS allowed headers",
    )

    # OpenAI settings
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o-mini", description="Model for conversations and corrections")
    openai_max_tokens: int = Field(default=500, description="Maximum tokens per request")
    openai_temperature: float = Field(default=0.7, description="Response randomness (0-2)")

    # Language settings
    supported_languages: list[str] = Field(
        default=["english", "ukrainian", "polish", "german"], description="List of supported language codes"
    )

    # Prompt settings
    prompts_directory: str = Field(default="backend/prompts", description="Directory containing prompt templates")
    prompt_validation_enabled: bool = Field(default=True, description="Whether to validate prompt templates at startup")

    # Context message settings
    context_chat_messages_num: int = Field(default=20, description="Maximum context messages for /chat endpoint")
    context_start_messages_num: int = Field(default=10, description="Maximum context messages for /start endpoint")

    # Request validation settings
    max_request_size_mb: int = Field(default=1, description="Maximum request size in MB")

    # Logging settings
    log_level: str = Field(default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")

    model_config = SettingsConfigDict(env_file=[".env", "backend/.env"], env_file_encoding="utf-8", extra="ignore")

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        valid_environments: list[Environment] = ["dev", "prod", "ci"]
        if v not in valid_environments:
            raise ValueError(f"ENVIRONMENT must be one of {valid_environments}")
        return v

    @field_validator("openai_api_key")
    @classmethod
    def validate_api_key_format(cls, v: str) -> str:
        if not v.startswith("sk-"):
            raise ValueError("OPENAI_API_KEY must start with 'sk-'")
        return v

    @field_validator("openai_temperature")
    @classmethod
    def validate_temperature_range(cls, v: float) -> float:
        if not 0 <= v <= 2:
            raise ValueError("OPENAI_TEMPERATURE must be between 0 and 2")
        return v

    @field_validator("openai_max_tokens")
    @classmethod
    def validate_max_tokens_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("OPENAI_MAX_TOKENS must be positive")
        return v

    @field_validator("supported_languages", mode="before")
    @classmethod
    def parse_supported_languages(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [lang.strip() for lang in v.split(",")]
        return v

    @field_validator("supported_languages")
    @classmethod
    def validate_languages_subset_of_enum(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("SUPPORTED_LANGUAGES cannot be empty")

        valid_languages = [lang.value for lang in Language]
        for lang in v:
            if lang not in valid_languages:
                raise ValueError(f"SUPPORTED_LANGUAGES contains unsupported language '{lang}' not in Language enum")
        return v

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins_format(cls, v: list[str]) -> list[str]:
        for origin in v:
            if not origin.startswith(("http://", "https://")):
                raise ValueError(
                    f"CORS_ORIGINS contains invalid origin '{origin}' that must start with http:// or https://"
                )
        return v

    @field_validator("cors_headers", mode="before")
    @classmethod
    def parse_cors_headers(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [header.strip() for header in v.split(",")]
        return v

    @field_validator("cors_headers")
    @classmethod
    def validate_cors_headers_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("CORS_HEADERS cannot be empty")
        return v

    @field_validator("max_request_size_mb")
    @classmethod
    def validate_max_request_size_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("MAX_REQUEST_SIZE_MB must be positive")
        return v

    @field_validator("context_chat_messages_num")
    @classmethod
    def validate_context_chat_messages_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("CONTEXT_CHAT_MESSAGES_NUM must be positive")
        return v

    @field_validator("context_start_messages_num")
    @classmethod
    def validate_context_start_messages_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("CONTEXT_START_MESSAGES_NUM must be positive")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v_upper
