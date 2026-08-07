"""
Health check endpoints for the backend service
"""
from fastapi import APIRouter
from datetime import datetime
import psutil
import os
from database import SessionLocal
from sqlalchemy import text

router = APIRouter()

def check_database_connection():
    """Check if database is accessible"""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return "connected"
    except Exception:
        return "disconnected"

def check_redis_connection():
    """Check if Redis is accessible"""
    try:
        import redis
        from config import settings
        r = redis.from_string(settings.REDIS_URL)
        r.ping()
        return "connected"
    except Exception:
        return "disconnected"

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "vehicle-detection-backend",
        "version": "1.0.0"
    }

@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with system metrics and service connectivity"""
    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Check service connections
        db_status = check_database_connection()
        redis_status = check_redis_connection()
        
        # Determine overall status
        overall_status = "healthy"
        if db_status == "disconnected" or redis_status == "disconnected":
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "service": "vehicle-detection-backend",
            "version": "1.0.0",
            "system": {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory.percent,
                "memory_available_mb": round(memory.available / 1024 / 1024, 2),
                "disk_usage_percent": disk.percent,
                "disk_free_gb": round(disk.free / 1024 / 1024 / 1024, 2)
            },
            "services": {
                "database": db_status,
                "redis": redis_status
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "service": "vehicle-detection-backend",
            "version": "1.0.0",
            "error": str(e)
        }

@router.get("/ready")
async def readiness_check():
    """Kubernetes-style readiness probe"""
    # Check if critical services are ready
    db_status = check_database_connection()
    redis_status = check_redis_connection()
    
    if db_status == "connected" and redis_status == "connected":
        return {"status": "ready"}
    else:
        # Return 503 Service Unavailable if not ready
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Service not ready")

@router.get("/live")
async def liveness_check():
    """Kubernetes-style liveness probe"""
    return {"status": "alive"}