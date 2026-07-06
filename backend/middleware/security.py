from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp
import time
import logging
from typing import Callable

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, *args, **kwargs):
        super().__init__(app, *args, **kwargs)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Add security headers
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Add process time header
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log request
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Process Time: {process_time:.3f}s"
        )
        
        return response