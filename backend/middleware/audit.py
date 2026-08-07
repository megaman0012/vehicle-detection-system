"""
Audit logging middleware for Vehicle Detection System
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import json
import logging
from utils.security import log_audit_event
from database import SessionLocal

logger = logging.getLogger("audit_middleware")

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip audit logging for certain paths
        skip_paths = ["/health", "/docs", "/openapi.json", "/redoc"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)
        
        # Get client information
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        
        user_agent = request.headers.get("User-Agent", "unknown")
        
        # Process request first to get response
        response = await call_next(request)
        
        # Log the request (in a real implementation, you would get user from token)
        # For now, we'll log basic information
        try:
            db = SessionLocal()
            # In a real implementation, you would extract user info from JWT token
            # and log more detailed information
            log_audit_event(
                db=db,
                user_id=None,  # Would be extracted from token
                action=f"{request.method}_{request.url.path.replace('/', '_').strip('_')}",
                resource_type="api_endpoint",
                resource_id=None,
                details={
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": str(request.query_params),
                    "status_code": response.status_code
                },
                ip_address=ip,
                user_agent=user_agent
            )
            db.close()
        except Exception as e:
            logger.error(f"Audit middleware error: {e}")
        
        return response