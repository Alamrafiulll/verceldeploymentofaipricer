import json
import logging
import time
import uuid
from collections.abc import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


logger = logging.getLogger("app")


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request.state.request_id = request_id
        started = time.perf_counter()
        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            payload = {
                "event": "request_completed",
                "request_id": request_id,
                "method": request.method,
                "route": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "user_id": getattr(request.state, "user_id", None),
            }
            logger.info(json.dumps(payload))
            response.headers["x-request-id"] = request_id
            return response
        except Exception as exc:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            payload = {
                "event": "request_failed",
                "request_id": request_id,
                "method": request.method,
                "route": request.url.path,
                "duration_ms": duration_ms,
                "user_id": getattr(request.state, "user_id", None),
                "error": str(exc),
            }
            logger.exception(json.dumps(payload))
            raise