"""
WhatsApp API Router for Vehicle Detection System
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import logging

from services.whatsapp_service import whatsapp_service, initialize_whatsapp_service
from utils.security import get_current_active_user
from models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)

# Pydantic models
class WhatsAppConfig(BaseModel):
    api_url: str = Field(..., description="Evolution API URL")
    api_key: str = Field(..., description="Evolution API Key")
    instance_name: str = Field(..., description="WhatsApp Instance Name")

class WhatsAppTestRequest(BaseModel):
    phone_number: str = Field(..., description="Phone number to send test message to")
    message: str = Field(default="Test message from Vehicle Detection System", description="Test message content")

class ParkingAlertRequest(BaseModel):
    phone_number: str = Field(..., description="Recipient phone number")
    license_plate: str = Field(..., description="Vehicle license plate")
    vehicle_type: str = Field(default="VEHÍCULO", description="Type of vehicle")
    confidence: float = Field(default=0.8, ge=0, le=1, description="Detection confidence")
    camera_name: str = Field(..., description="Name of the camera that detected the vehicle")

class CameraOfflineAlertRequest(BaseModel):
    phone_number: str = Field(..., description="Recipient phone number")
    camera_name: str = Field(..., description="Name of the offline camera")

class SystemAlertRequest(BaseModel):
    phone_number: str = Field(..., description="Recipient phone number")
    alert_type: str = Field(..., description="Type of system alert")
    description: str = Field(..., description="Description of the alert")

class WhatsAppResponse(BaseModel):
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    response: Optional[Dict[str, Any]] = None

# Initialize WhatsApp service (in a real app, this would come from environment variables)
# For now, we'll initialize with placeholder values - should be configured via API
try:
    whatsapp_service = initialize_whatsapp_service(
        api_url="http://localhost:8080",  # Default Evolution API URL
        api_key="your-api-key-here",
        instance_name="vehicle-detection"
    )
except Exception as e:
    logger.warning(f"Could not initialize WhatsApp service: {e}")
    whatsapp_service = None

@router.post("/configure", response_model=Dict[str, str])
async def configure_whatsapp(
    config: WhatsAppConfig,
    current_user: User = Depends(get_current_active_user)
):
    """
    Configure WhatsApp service settings
    Requires admin privileges
    """
    # In a real implementation, you would check if user is admin
    # and save the configuration to database or secure storage
    
    global whatsapp_service
    try:
        whatsapp_service = initialize_whatsapp_service(
            api_url=config.api_url,
            api_key=config.api_key,
            instance_name=config.instance_name
        )
        
        logger.info(f"WhatsApp service configured by user {current_user.email}")
        return {
            "message": "WhatsApp service configured successfully",
            "status": "configured"
        }
    except Exception as e:
        logger.error(f"Failed to configure WhatsApp service: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to configure WhatsApp service: {str(e)}")

@router.post("/test", response_model=WhatsAppResponse)
async def test_whatsapp_connection(
    current_user: User = Depends(get_current_active_user)
):
    """
    Test WhatsApp API connection
    """
    if not whatsapp_service:
        raise HTTPException(
            status_code=503, 
            detail="WhatsApp service not configured. Please configure it first."
        )
    
    try:
        result = await whatsapp_service.test_connection()
        return WhatsAppResponse(**result)
    except Exception as e:
        logger.error(f"WhatsApp connection test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send-message", response_model=WhatsAppResponse)
async def send_whatsapp_message(
    request: WhatsAppTestRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """
    Send a WhatsApp message
    """
    if not whatsapp_service:
        raise HTTPException(
            status_code=503, 
            detail="WhatsApp service not configured. Please configure it first."
        )
    
    # Send message in background to avoid blocking the API response
    background_tasks.add_task(
        whatsapp_service.send_message,
        request.phone_number,
        request.message
    )
    
    return WhatsAppResponse(
        success=True,
        message="Message queued for sending"
    )

@router.post("/send-parking-alert", response_model=WhatsAppResponse)
async def send_parking_alert(
    request: ParkingAlertRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """
    Send a parking alert via WhatsApp
    """
    if not whatsapp_service:
        raise HTTPException(
            status_code=503, 
            detail="WhatsApp service not configured. Please configure it first."
        )
    
    vehicle_info = {
        "license_plate": request.license_plate,
        "vehicle_type": request.vehicle_type,
        "confidence": request.confidence
    }
    
    camera_info = {
        "name": request.camera_name
    }
    
    # Send alert in background
    background_tasks.add_task(
        whatsapp_service.send_parking_alert,
        request.phone_number,
        vehicle_info,
        camera_info
    )
    
    return WhatsAppResponse(
        success=True,
        message="Parking alert queued for sending"
    )

@router.post("/send-camera-offline-alert", response_model=WhatsAppResponse)
async def send_camera_offline_alert(
    request: CameraOfflineAlertRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """
    Send a camera offline alert via WhatsApp
    """
    if not whatsapp_service:
        raise HTTPException(
            status_code=503, 
            detail="WhatsApp service not configured. Please configure it first."
        )
    
    camera_info = {
        "name": request.camera_name
    }
    
    # Send alert in background
    background_tasks.add_task(
        whatsapp_service.send_camera_offline_alert,
        request.phone_number,
        camera_info
    )
    
    return WhatsAppResponse(
        success=True,
        message="Camera offline alert queued for sending"
    )

@router.post("/send-system-alert", response_model=WhatsAppResponse)
async def send_system_alert(
    request: SystemAlertRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """
    Send a system alert via WhatsApp
    """
    if not whatsapp_service:
        raise HTTPException(
            status_code=503, 
            detail="WhatsApp service not configured. Please configure it first."
        )
    
    alert_info = {
        "type": request.alert_type,
        "description": request.description
    }
    
    # Send alert in background
    background_tasks.add_task(
        whatsapp_service.send_system_alert,
        request.phone_number,
        alert_info
    )
    
    return WhatsAppResponse(
        success=True,
        message="System alert queued for sending"
    )

@router.get("/status", response_model=Dict[str, Any])
async def get_whatsapp_status(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get WhatsApp service status
    """
    if not whatsapp_service:
        return {
            "configured": False,
            "message": "WhatsApp service not configured"
        }
    
    # In a real implementation, you might want to check if the service is actually working
    return {
        "configured": True,
        "instance_name": whatsapp_service.instance_name,
        "api_url": whatsapp_service.api_url,
        "message": "WhatsApp service is configured"
    }