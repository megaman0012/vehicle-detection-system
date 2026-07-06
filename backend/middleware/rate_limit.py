"""
Rate limiting middleware for Vehicle Detection System
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import time
import logging
from app.utils.security import check_api_rate_limit

logger = logging.getLogger("rate_limit")

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period

    async def dispatch(self, request: Request, call_next):
        # Get client IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0]
        else:
            ip = request.client.host if request.client else "unknown"
        
        # Check rate limit
        if not check_api_rate_limit(ip):
            logger.warning(f"Rate limit exceeded for IP: {ip}")
            return Response(
                content='{"detail": "Rate limit exceeded"}',
                status_code=429,
                media_type="application/json"
            )
        
        # Process request
        response = await call_next(request)
        return response