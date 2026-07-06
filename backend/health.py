"""
Health check endpoints for the backend service
"""
from fastapi import APIRouter
from datetime import datetime
import psutil
import os

router = APIRouter()

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
    """Detailed health check with system metrics"""
    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Check database connection (simplified)
        db_status = "connected"  # In a real implementation, check actual DB connection
        
        # Check Redis connection (simplified)
        redis_status = "connected"  # In a real implementation, check actual Redis connection
        
        return {
            "status": "healthy",
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
    # In a real implementation, check if all dependencies are ready
    return {"status": "ready"}

@router.get("/live")
async def liveness_check():
    """Kubernetes-style liveness probe"""
    return {"status": "alive"}