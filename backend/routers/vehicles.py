from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from uuid import UUID

from database import get_db
from models.vehicle import DetectedVehicle, VehicleType
from models.camera import Camera
from models.user import User
from schemas.vehicle import DetectedVehicleCreate, DetectedVehicleUpdate, DetectedVehicleResponse
from utils.auth import get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[DetectedVehicleResponse])
async def read_vehicles(
    skip: int = 0,
    limit: int = 100,
    vehicle_type: Optional[VehicleType] = None,
    is_parked: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all detected vehicles"""
    query = db.query(DetectedVehicle)
    
    # Filter by user's cameras unless admin
    if current_user.role != "admin":
        query = query.join(DetectedVehicle.camera).filter(Camera.owner_id == current_user.id)
    
    # Apply filters
    if vehicle_type:
        query = query.filter(DetectedVehicle.vehicle_type == vehicle_type)
    if is_parked is not None:
        query = query.filter(DetectedVehicle.is_parked == is_parked)
    
    vehicles = query.offset(skip).limit(limit).all()
    return vehicles

@router.post("/", response_model=DetectedVehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    vehicle: DetectedVehicleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new detected vehicle"""
    if current_user.role not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Verify camera exists
    camera = db.query(Camera).filter(Camera.id == vehicle.camera_id).first()
    if camera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )

    # Upsert by vehicle_id + camera_id: the AI service reuses track IDs after a
    # restart (T-1, T-2, ...), so the same vehicle_id may already exist.
    db_vehicle = db.query(DetectedVehicle).filter(
        DetectedVehicle.vehicle_id == vehicle.vehicle_id,
        DetectedVehicle.camera_id == vehicle.camera_id,
    ).first()

    data = vehicle.dict()
    if db_vehicle is None:
        db_vehicle = DetectedVehicle(**data)
        db.add(db_vehicle)
    else:
        for field, value in data.items():
            setattr(db_vehicle, field, value)
        db_vehicle.last_seen = datetime.now(timezone.utc)

    # Track parking timing
    now = datetime.now(timezone.utc)
    if data.get("is_parked") and db_vehicle.park_start_time is None:
        db_vehicle.park_start_time = now
    elif not data.get("is_parked") and db_vehicle.park_start_time is not None:
        parked_until = db_vehicle.park_start_time
        if parked_until.tzinfo is None:
            parked_until = parked_until.replace(tzinfo=timezone.utc)
        elapsed = now - parked_until
        if elapsed.total_seconds() > 0:
            if db_vehicle.total_park_time is None:
                db_vehicle.total_park_time = timedelta(0)
            db_vehicle.total_park_time = (db_vehicle.total_park_time or timedelta(0)) + elapsed
        db_vehicle.park_start_time = None

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        db_vehicle = db.query(DetectedVehicle).filter(
            DetectedVehicle.vehicle_id == vehicle.vehicle_id,
            DetectedVehicle.camera_id == vehicle.camera_id,
        ).first()
        if db_vehicle is None:
            raise
        for field, value in data.items():
            setattr(db_vehicle, field, value)
        db_vehicle.last_seen = datetime.now(timezone.utc)
        db.commit()

    db.refresh(db_vehicle)
    return db_vehicle

@router.get("/{vehicle_id}", response_model=DetectedVehicleResponse)
async def read_vehicle(
    vehicle_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific detected vehicle by ID"""
    vehicle = db.query(DetectedVehicle).filter(DetectedVehicle.id == vehicle_id).first()
    if vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )
    
    # Check permissions
    if current_user.role != "admin" and vehicle.camera.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return vehicle

@router.put("/{vehicle_id}", response_model=DetectedVehicleResponse)
async def update_vehicle(
    vehicle_id: UUID,
    vehicle: DetectedVehicleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a detected vehicle"""
    db_vehicle = db.query(DetectedVehicle).filter(DetectedVehicle.id == vehicle_id).first()
    if db_vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )
    
    # Check permissions
    if current_user.role != "admin" and db_vehicle.camera.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Update fields
    update_data = vehicle.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_vehicle, field, value)
    
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle

@router.get("/parked/current", response_model=List[DetectedVehicleResponse])
async def get_currently_parked_vehicles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get currently parked vehicles"""
    query = db.query(DetectedVehicle).filter(DetectedVehicle.is_parked == True)
    
    # Filter by user's cameras unless admin
    if current_user.role != "admin":
        query = query.join(DetectedVehicle.camera).filter(Camera.owner_id == current_user.id)
    
    vehicles = query.all()
    return vehicles