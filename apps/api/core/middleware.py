import redis.asyncio as redis
from starlette.datastructures import Headers
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from .config import settings
from .observability import trace_id_cv
from .utils import generate_uuid


class TraceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = request.headers.get("X-Trace-Id") or generate_uuid()
        request.state.trace_id = trace_id

        token = trace_id_cv.set(trace_id)
        try:
            response = await call_next(request)
            response.headers["X-Trace-Id"] = trace_id
            return response
        finally:
            trace_id_cv.reset(token)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path not in ("/docs", "/redoc", "/openapi.json"):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; frame-ancestors 'none'; object-src 'none'"
            )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


class OriginEnforcementMiddleware:
    """Reject cross-origin browser mutations outside the configured allowlist."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["method"] not in {
            "GET",
            "HEAD",
            "OPTIONS",
            "TRACE",
        }:
            origin = Headers(scope=scope).get("origin")
            if origin and origin not in settings.cors_origins:
                response = JSONResponse(
                    status_code=403,
                    content={"title": "Forbidden", "detail": "Origin is not allowed"},
                )
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)


_redis_client = None


def get_redis_client():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url)
    return _redis_client


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Redis-backed idempotency middleware to prevent concurrent double-clicks.
    For full DB persistence, use `check_idempotency` in the route.
    """

    async def dispatch(self, request: Request, call_next):
        if request.method not in ("POST", "PUT", "PATCH"):
            return await call_next(request)

        idem_key = request.headers.get("Idempotency-Key")
        if not idem_key:
            return await call_next(request)

        client = get_redis_client()
        lock_key = f"idempotency_lock:{idem_key}"

        # Try to acquire lock with 10 min TTL (setnx)
        acquired = await client.set(lock_key, "1", nx=True, ex=600)
        if not acquired:
            return JSONResponse(
                status_code=409,
                content={"title": "Conflict", "detail": "Request already in progress"},
            )

        try:
            response = await call_next(request)
            return response
        finally:
            # Allow key to be used again for retries, but DB idempotency will handle the cache
            await client.delete(lock_key)
