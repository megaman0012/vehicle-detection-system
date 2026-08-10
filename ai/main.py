"""
Main FastAPI application for AI Service
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from app.routers import detection, health

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Vehicle Detection System AI Service...")
    # Initialize AI models here in a real implementation
    yield
    # Shutdown
    logger.info("Shutting down Vehicle Detection System AI Service...")

# Create FastAPI app
app = FastAPI(
    title="Vehicle Detection System AI Service",
    description="AI service for vehicle detection, tracking, and license plate recognition",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(detection.router, prefix="/api/detection", tags=["detection"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Vehicle Detection System AI Service",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Global exception handler
from datetime import datetime

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception handler caught: {exc}")
    return {
        "error": "Internal server error",
        "message": "An unexpected error occurred",
        "timestamp": datetime.now().isoformat()
    }