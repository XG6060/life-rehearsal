"""FastAPI 中间件"""

from __future__ import annotations

import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.utils.logger import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(self, request: Request, call_next):
        start = time.time()
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        response: Response = await call_next(request)
        elapsed = int((time.time() - start) * 1000)

        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"→ {response.status_code} ({elapsed}ms)"
        )
        response.headers["X-Request-ID"] = request_id
        return response


class CORSMiddleware(BaseHTTPMiddleware):
    """CORS 中间件"""

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            response = Response()
        else:
            response = await call_next(request)

        response.headers["Access-Control-Allow-Origin"] = "http://localhost:8501"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-User-Id"
        return response
