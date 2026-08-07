"""
Health check endpoints for the AI service
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
        "service": "vehicle-detection-ai",
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
        
        # Check if GPU is available (simplified)
        gpu_available = False  # In a real implementation, check actual GPU availability
        gpu_memory_used = 0
        gpu_memory_total = 0
        
        try:
            import torch
            if torch.cuda.is_available():
                gpu_available = True
                gpu_memory_used = torch.cuda.memory_allocated() / 1024 / 1024  # MB
                gpu_memory_total = torch.cuda.get_device_properties(0).total_memory / 1024 / 1024  # MB
        except ImportError:
            pass  # torch not available
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "vehicle-detection-ai",
            "version": "1.0.0",
            "system": {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory.percent,
                "memory_available_mb": round(memory.available / 1024 / 1024, 2),
                "disk_usage_percent": disk.percent,
                "disk_free_gb": round(disk.free / 1024 / 1024 / 1024, 2)
            },
            "ai_services": {
                "gpu_available": gpu_available,
                "gpu_memory_used_mb": round(gpu_memory_used, 2),
                "gpu_memory_total_mb": round(gpu_memory_total, 2),
                "yolo_model_loaded": False,  # Would check actual model loading
                "ocr_initialized": False     # Would check actual OCR initialization
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "service": "vehicle-detection-ai",
            "version": "1.0.0",
            "error": str(e)
        }

@router.get("/ready")
async def readiness_check():
    """Kubernetes-style readiness probe"""
    return {"status": "ready"}

@router.get("/live")
async def liveness_check():
    """Kubernetes-style liveness probe"""
    return {"status": "alive"}