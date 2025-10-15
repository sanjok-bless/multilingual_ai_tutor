"""Request size validation middleware."""

from collections.abc import Callable

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class RequestSizeMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce maximum request size limits."""

    def __init__(self, app: ASGIApp, max_size_bytes: int) -> None:
        super().__init__(app)
        self.max_size = max_size_bytes

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        """Validate request size and process if within limits."""
        if request.headers.get("content-length"):
            content_length = int(request.headers["content-length"])
            if content_length > self.max_size:
                raise HTTPException(413, "Request too large")
        return await call_next(request)
