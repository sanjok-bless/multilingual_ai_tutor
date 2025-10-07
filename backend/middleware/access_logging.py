"""Access logging middleware with structured JSON output."""

import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from backend import observability

logger = observability.get_logger(__name__)


class AccessLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured HTTP access logging."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        """Process request and log access details."""
        start_time = time.perf_counter()
        response = await call_next(request)
        duration = (time.perf_counter() - start_time) * 1000

        logger.info(
            "HTTP request",
            method=request.method,
            path=request.url.path,
            code=response.status_code,
            ms=round(duration, 2),
            ip=request.client.host if request.client else None,
        )

        return response
