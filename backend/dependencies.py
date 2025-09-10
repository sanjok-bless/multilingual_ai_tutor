"""FastAPI dependency providers for application configuration."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from backend.config import AppConfig
from backend.llms.langchain_client import LangChainClient


@lru_cache
def get_config() -> AppConfig:
    """Get cached application configuration."""
    return AppConfig()


@lru_cache
def get_langchain_client() -> LangChainClient:
    """Get cached LangChain client for AI operations."""
    config = get_config()
    return LangChainClient(config)


# Type aliases for dependency injection
ConfigDep = Annotated[AppConfig, Depends(get_config)]
LangChainDep = Annotated[LangChainClient, Depends(get_langchain_client)]
