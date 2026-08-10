from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from database import get_db
from models.vehicle import DetectedVehicle, VehicleType
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

@router.get("/{vehicle_id}", response_model=DetectedVehicleResponse)
async def read_vehicle(
    vehicle_id: int,
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
    vehicle_id: int,
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