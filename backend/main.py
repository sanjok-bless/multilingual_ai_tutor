"""FastAPI application for Multilingual AI Tutor."""

import sys
from collections.abc import Callable

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from backend.api.v1.chat import router as chat_router
from backend.api.v1.health import router as health_router
from backend.api.v1.metrics import router as metrics_router
from backend.dependencies import get_config


class RequestSizeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, max_size_bytes: int) -> None:
        super().__init__(app)
        self.max_size = max_size_bytes

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        if request.headers.get("content-length"):
            content_length = int(request.headers["content-length"])
            if content_length > self.max_size:
                raise HTTPException(413, "Request too large")
        return await call_next(request)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    config = get_config()

    # Disable docs endpoints in production environment
    docs_url = "/docs" if config.environment == "dev" else None
    redoc_url = "/redoc" if config.environment == "dev" else None

    app = FastAPI(
        title="Multilingual AI Tutor",
        description="AI-powered language coach with real-time conversational practice",
        version="0.1.0",
        docs_url=docs_url,
        redoc_url=redoc_url,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=config.cors_headers,
    )

    app.add_middleware(RequestSizeMiddleware, max_size_bytes=config.max_request_size_mb * 1024 * 1024)

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")
    app.include_router(metrics_router, prefix="/api/v1")

    return app


def get_application() -> FastAPI:
    return create_app()


def _is_test_environment() -> bool:
    return "pytest" in sys.modules


# Only create app instance when not in test environment or when explicitly called
# This prevents configuration loading during test discovery/imports
if not _is_test_environment():
    app = get_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
