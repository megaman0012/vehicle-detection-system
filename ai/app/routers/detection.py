"""
Detection endpoints for the AI service
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def detection_root():
    """Root endpoint for detection service"""
    return {"message": "Vehicle Detection AI Service"}

# Placeholder for actual detection endpoints
# These would be implemented based on the actual AI service functionality
