"""A small in-memory, per-IP fixed-window rate limiter for abuse-prone auth
endpoints. Single-instance (fine for the current deploy); a multi-instance
deployment should move the counters to Redis. Disabled in dev/test envs so it
never interferes with the test suite or local iteration."""

from __future__ import annotations

import os
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

# path -> (max requests, window seconds)
_LIMITS: dict[str, tuple[int, int]] = {
    "/auth/login": (10, 60),
    "/auth/signup": (5, 60),
    "/auth/reset/request": (5, 60),
}
_DEV_ENVS = {"dev", "test", "local", "ci"}


def _enforcing() -> bool:
    return os.environ.get("CAREEROS_ENV", "").lower() not in _DEV_ENVS


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._hits: dict[tuple[str, str], deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next) -> Response:
        limit = _LIMITS.get(request.url.path)
        if limit and request.method == "POST" and _enforcing():
            max_requests, window = limit
            ip = request.client.host if request.client else "unknown"
            key = (ip, request.url.path)
            now = time.monotonic()
            hits = self._hits[key]
            while hits and hits[0] <= now - window:
                hits.popleft()
            if len(hits) >= max_requests:
                return JSONResponse(
                    {"detail": "Too many requests — please slow down and try again shortly."},
                    status_code=429,
                    headers={"Retry-After": str(window)},
                )
            hits.append(now)
        return await call_next(request)
