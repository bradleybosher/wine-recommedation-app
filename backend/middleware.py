"""Request-logging middleware and global exception handlers for the FastAPI app."""
import logging
import time
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("sommelier.api")


def install(app: FastAPI) -> None:
    """Attach the request logger and exception handlers to `app`."""

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start = time.perf_counter()
        client_ip = request.client.host if request.client else "unknown"
        logger.info(
            "request_start id=%s method=%s path=%s ip=%s",
            request_id,
            request.method,
            request.url.path,
            client_ip,
        )
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            logger.exception(
                "request_error id=%s method=%s path=%s elapsed_ms=%s",
                request_id,
                request.method,
                request.url.path,
                elapsed_ms,
            )
            raise

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "request_end id=%s method=%s path=%s status=%s elapsed_ms=%s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        response.headers["X-Request-ID"] = request_id
        return response

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Preserve status codes and bodies for intentional HTTP errors."""
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception(
            "unhandled_exception path=%s err=%s", request.url.path, type(exc).__name__
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "error_type": type(exc).__name__},
        )
