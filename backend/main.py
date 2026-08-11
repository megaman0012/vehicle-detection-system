"""
Main FastAPI application for Vehicle Detection System
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from routers import auth, users, cameras, vehicles, events, reports, config, whatsapp, system, websocket, zones
from health import router as health_router
from database import engine
from models.base import Base
from middleware.rate_limit import RateLimitMiddleware
from middleware.audit import AuditMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
# Base.metadata.create_all(bind=engine)  # Commented out for testing - would work in Docker environment

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Vehicle Detection System Backend...")
    yield
    # Shutdown
    logger.info("Shutting down Vehicle Detection System Backend...")

# Create FastAPI app
app = FastAPI(
    title="Vehicle Detection System API",
    description="API for intelligent vehicle detection and license plate recognition",
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

# Add custom middlewares
app.add_middleware(AuditMiddleware)
app.add_middleware(RateLimitMiddleware, calls=100, period=60)  # 100 requests per minute

# Include routers
app.include_router(health_router, tags=["health"])
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(cameras.router, prefix="/api/cameras", tags=["cameras"])
app.include_router(zones.router, prefix="/api/zones", tags=["zones"])
app.include_router(vehicles.router, prefix="/api/vehicles", tags=["vehicles"])
app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(config.router, prefix="/api/config", tags=["configuration"])
app.include_router(whatsapp.router, prefix="/api/whatsapp", tags=["whatsapp"])
app.include_router(system.router, prefix="/api/system", tags=["system"])
app.include_router(websocket.router, prefix="/api/ws", tags=["websocket"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Vehicle Detection System API",
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