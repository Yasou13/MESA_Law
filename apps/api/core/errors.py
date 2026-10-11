import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm.exc import StaleDataError

logger = logging.getLogger(__name__)


class ProblemException(Exception):
    def __init__(self, status: int, title: str, detail: str, type: str = "about:blank"):
        self.status = status
        self.title = title
        self.detail = detail
        self.type = type


async def problem_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, ProblemException):
        raise exc
    return JSONResponse(
        status_code=exc.status,
        content={
            "type": exc.type,
            "title": exc.title,
            "status": exc.status,
            "detail": exc.detail,
            "instance": str(request.url),
        },
        media_type="application/problem+json",
    )


async def stale_data_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, StaleDataError):
        raise exc
    return JSONResponse(
        status_code=409,
        content={
            "type": "about:blank",
            "title": "Conflict",
            "status": 409,
            "detail": "The record was modified by another request. Reload and retry.",
            "instance": str(request.url),
        },
        media_type="application/problem+json",
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception occurred")
    return JSONResponse(
        status_code=500,
        content={
            "type": "about:blank",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred.",
            "instance": str(request.url),
        },
        media_type="application/problem+json",
    )
