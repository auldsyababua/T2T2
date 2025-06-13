from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from utils.cache import cache
from utils.logging import setup_logger

logger = setup_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple IP-based rate-limiting middleware.

    Defaults: 100 requests per 60-second sliding window per client IP.
    The limits can be tweaked when adding the middleware:

    ```python
    app.add_middleware(RateLimitMiddleware, max_requests=50, window_seconds=30)
    ```
    """

    def __init__(self, app, *, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    # ------------------------------------------------------------------
    # Starlette hook
    # ------------------------------------------------------------------

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        identifier = request.client.host if request.client else "anonymous"
        current_window = int(time.time() // self.window_seconds)
        key = f"rl:{identifier}:{current_window}"

        try:
            count_raw = await cache.get(key)
            count = int(count_raw) if count_raw is not None else 0
        except Exception as exc:  # pragma: no cover
            logger.warning("RateLimit: cache backend failed – treating as 0 (%s)", exc)
            count = 0

        if count >= self.max_requests:
            logger.warning("Rate limit exceeded for %s", identifier)
            headers = {
                "Retry-After": str(self.window_seconds),
                "X-RateLimit-Limit": str(self.max_requests),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str((current_window + 1) * self.window_seconds),
            }
            return JSONResponse(
                {"detail": "Rate limit exceeded"}, status_code=429, headers=headers
            )

        # update the counter – no await for speed if cache set fails swallow error
        try:
            await cache.set(key, count + 1, ttl=self.window_seconds)
        except Exception as exc:  # pragma: no cover
            logger.warning("RateLimit: cache backend set failed – %s", exc)

        response = await call_next(request)
        remaining = max(self.max_requests - (count + 1), 0)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(
            (current_window + 1) * self.window_seconds
        )
        return response
