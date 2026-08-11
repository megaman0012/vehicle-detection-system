"""
Detection endpoints for the AI service.

These let the backend (or an operator) start/stop per-camera processing and
query the latest results produced by the detection pipeline.
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.ai_service import ai_service

logger = logging.getLogger(__name__)

router = APIRouter()


class StartCameraRequest(BaseModel):
    rtsp_url: str
    username: Optional[str] = None
    password: Optional[str] = None


class StopCameraRequest(BaseModel):
    camera_id: str


@router.get("/")
async def detection_root():
    """Root endpoint for detection service."""
    return {
        "message": "Vehicle Detection AI Service",
        "endpoints": [
            "GET  /api/detection/status",
            "POST /api/detection/cameras/{camera_id}/start",
            "POST /api/detection/cameras/{camera_id}/stop",
            "GET  /api/detection/cameras/{camera_id}/results",
        ],
    }


@router.get("/status")
async def detection_status():
    """Global status of the AI service and its detector."""
    return ai_service.get_status()


@router.post("/cameras/{camera_id}/start")
async def start_camera(camera_id: str, request: StartCameraRequest):
    """Start processing an RTSP stream for the given camera."""
    if not request.rtsp_url:
        raise HTTPException(status_code=400, detail="rtsp_url is required")
    ai_service.start_camera_processing(
        camera_id,
        request.rtsp_url,
        request.username,
        request.password,
    )
    return {"camera_id": camera_id, "status": "started", "rtsp_url": request.rtsp_url}


@router.post("/cameras/{camera_id}/stop")
async def stop_camera(camera_id: str):
    """Stop processing the given camera."""
    if camera_id not in ai_service.processing_threads:
        raise HTTPException(status_code=404, detail="Camera is not being processed")
    ai_service.stop_camera_processing(camera_id)
    return {"camera_id": camera_id, "status": "stopped"}


@router.get("/cameras/{camera_id}/results")
async def get_camera_results(camera_id: str):
    """Get the latest detection results for a camera."""
    if camera_id not in ai_service.processing_threads:
        raise HTTPException(status_code=404, detail="Camera is not being processed")
    results = ai_service.get_latest_results(camera_id)
    if results is None:
        raise HTTPException(status_code=204, detail="No results yet")
    return results
