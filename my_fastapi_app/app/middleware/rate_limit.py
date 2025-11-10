"""Redis-backed rate limit middleware with in-memory fallback.

Uses a simple fixed-window counter per IP. If `REDIS_URL` is configured in
`app.core.config`, the middleware uses Redis INCR+EXPIRE which works across
processes and hosts. Otherwise falls back to an in-memory limiter (not
recommended for production).
"""

import time
import logging
from collections import deque
from typing import Deque, Dict, Optional

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    """Simple in-memory per-IP limiter (same as before)."""

    def __init__(self, requests: int, window_seconds: int) -> None:
        self.requests = requests
        self.window = window_seconds
        self._storage: Dict[str, Deque[float]] = {}

    def is_allowed(self, key: str) -> (bool, int):
        now = time.time()
        q = self._storage.get(key)
        if q is None:
            q = deque()
            self._storage[key] = q

        while q and (now - q[0]) > self.window:
            q.popleft()

        if len(q) >= self.requests:
            retry_after = int(self.window - (now - q[0])) if q else self.window
            return False, retry_after

        q.append(now)
        return True, 0


class RedisRateLimiter:
    """Redis-based fixed-window limiter using INCR + EXPIRE.

    Key format: `rl:{ip}:{window_ts}` where window_ts = int(now // window_seconds)
    """

    def __init__(self, redis_client, requests: int, window_seconds: int) -> None:
        self.redis = redis_client
        self.requests = requests
        self.window = window_seconds

    async def is_allowed(self, key: str) -> (bool, int):
        # Use a per-window key to avoid race conditions with EXPIRE
        now = int(time.time())
        window_ts = now // self.window
        redis_key = f"rl:{key}:{window_ts}"

        try:
            current = await self.redis.incr(redis_key)
            if current == 1:
                # First increment in this window: set expiry
                await self.redis.expire(redis_key, self.window)

            if current > self.requests:
                ttl = await self.redis.ttl(redis_key)
                retry_after = int(ttl if ttl and ttl > 0 else self.window)
                return False, retry_after

            return True, 0

        except Exception as exc:  # pragma: no cover - Redis may be unavailable
            logger.exception("Redis rate limiter error, falling back to allow: %s", exc)
            # Fail open: allow requests when Redis errors to avoid outages,
            # caller can choose to fail-closed instead.
            return True, 0


class RateLimitMiddleware:
    """Rate limiting middleware; uses Redis when configured else in-memory."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.limiter = None

        # Lazy import to avoid importing aioredis at module import time
        redis_url = getattr(settings, "REDIS_URL", None)
        if redis_url:
            try:
                import aioredis

                self.redis = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True)
                self.limiter = RedisRateLimiter(
                    self.redis,
                    requests=settings.RATE_LIMIT_REQUESTS,
                    window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
                )
                logger.info("Using Redis rate limiter (url=%s)", redis_url)
            except Exception:
                logger.exception("Failed to initialize aioredis, falling back to in-memory limiter")
                self.limiter = InMemoryRateLimiter(
                    requests=settings.RATE_LIMIT_REQUESTS,
                    window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
                )
        else:
            logger.info("No REDIS_URL configured — using in-memory rate limiter")
            self.limiter = InMemoryRateLimiter(
                requests=settings.RATE_LIMIT_REQUESTS,
                window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
            )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)

        xff = request.headers.get("x-forwarded-for")
        if xff:
            client_ip = xff.split(",")[0].strip()
        else:
            client_ip = scope.get("client")[0] if scope.get("client") else "unknown"

        # Call appropriate limiter (Redis is async; in-memory is sync)
        if isinstance(self.limiter, RedisRateLimiter):
            allowed, retry_after = await self.limiter.is_allowed(client_ip)
        else:
            allowed, retry_after = self.limiter.is_allowed(client_ip)

        if not allowed:
            payload = {"detail": "Too Many Requests"}
            headers = {"Retry-After": str(retry_after)}
            response = JSONResponse(payload, status_code=429, headers=headers)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
