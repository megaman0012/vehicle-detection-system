from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import platform
import psutil
import datetime

from database import get_db
from utils.auth import get_current_active_user
from services.system_service import SystemService

router = APIRouter()

@router.get("/status")
async def get_system_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get overall system status"""
    if current_user.role not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    system_service = SystemService(db)
    status = await system_service.get_system_status()
    return status

@router.get("/health")
async def get_health_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed health status"""
    if current_user.role not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    system_service = SystemService(db)
    health = await system_service.get_health_status()
    return health

@router.get("/metrics")
async def get_system_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get system metrics"""
    if current_user.role not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Database metrics
    from database import engine
    from sqlalchemy import text
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            
            result = conn.execute(text("SELECT COUNT(*) FROM cameras"))
            camera_count = result.scalar()
            
            result = conn.execute(text("SELECT COUNT(*) FROM events WHERE timestamp > NOW() - INTERVAL '24 hours'"))
            event_count_24h = result.scalar()
    except Exception:
        user_count = 0
        camera_count = 0
        event_count_24h = 0
    
    return {
        "system": {
            "cpu_usage_percent": cpu_percent,
            "memory_usage_percent": memory.percent,
            "memory_available_mb": memory.available / 1024 / 1024,
            "disk_usage_percent": disk.percent,
            "disk_free_gb": disk.free / 1024 / 1024 / 1024,
            "boot_time": datetime.datetime.fromtimestamp(psutil.boot_time()).isoformat(),
            "platform": platform.platform(),
            "python_version": platform.python_version()
        },
        "database": {
            "user_count": user_count,
            "camera_count": camera_count,
            "events_last_24h": event_count_24h
        },
        "timestamp": datetime.datetime.now().isoformat()
    }

@router.get("/version")
async def get_version():
    """Get system version"""
    return {
        "name": "Sistema Inteligente de Detección de Vehículos Estacionados",
        "version": "1.0.0",
        "build_date": "2026-07-04",
        "description": "Sistema para detectar vehículos estacionados usando cámaras Hikvision y IA"
    }

@router.post("/restart-service/{service_name}")
async def restart_service(
    service_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Restart a system service"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # In a real implementation, this would interact with systemctl or Docker
    # For now, we'll just return a success message
    system_service = SystemService(db)
    result = await system_service.restart_service(service_name)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart service: {result['error']}"
        )
    
    return result

@router.get("/logs")
async def get_system_logs(
    lines: int = 100,
    level: str = "INFO",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get system logs"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    system_service = SystemService(db)
    logs = await system_service.get_logs(lines=lines, level=level)
    return {"logs": logs}