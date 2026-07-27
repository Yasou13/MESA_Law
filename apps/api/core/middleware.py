from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from .utils import generate_uuid


class TraceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = request.headers.get("X-Trace-Id") or generate_uuid()
        request.state.trace_id = trace_id
        response = await call_next(request)
        response.headers["X-Trace-Id"] = trace_id
        return response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'; object-src 'none'"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

import asyncio
from starlette.responses import JSONResponse

_idempotency_locks = set()

class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    In-memory idempotency middleware to prevent concurrent double-clicks.
    For full DB persistence, use `check_idempotency` in the route.
    """
    async def dispatch(self, request: Request, call_next):
        if request.method not in ("POST", "PUT", "PATCH"):
            return await call_next(request)
            
        idem_key = request.headers.get("Idempotency-Key")
        if not idem_key:
            return await call_next(request)
            
        if idem_key in _idempotency_locks:
            return JSONResponse(
                status_code=409, 
                content={"title": "Conflict", "detail": "Request already in progress"}
            )
            
        _idempotency_locks.add(idem_key)
        try:
            response = await call_next(request)
            return response
        finally:
            # Allow key to be used again for retries, but DB idempotency will handle the cache
            _idempotency_locks.discard(idem_key)

