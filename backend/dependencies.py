"""FastAPI dependency providers for application configuration."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from backend.config import AppConfig


@lru_cache
def get_config() -> AppConfig:
    """Get cached application configuration."""
    return AppConfig()


# Type alias for dependency injection
ConfigDep = Annotated[AppConfig, Depends(get_config)]
