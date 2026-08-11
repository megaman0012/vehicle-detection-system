from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID

from database import get_db
from models.event import Event, EventType
from models.camera import Camera
from models.vehicle import DetectedVehicle
from models.zone import Zone
from models.user import User
from schemas.event import EventCreate, EventUpdate, EventResponse
from utils.auth import get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[EventResponse])
async def read_events(
    skip: int = 0,
    limit: int = 100,
    event_type: Optional[EventType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all events"""
    query = db.query(Event)
    
    # Filter by user's cameras unless admin
    if current_user.role != "admin":
        query = query.join(Event.camera).filter(Camera.owner_id == current_user.id)
    
    # Apply filters
    if event_type:
        query = query.filter(Event.event_type == event_type)
    if start_date:
        query = query.filter(Event.timestamp >= start_date)
    if end_date:
        query = query.filter(Event.timestamp <= end_date)
    
    events = query.order_by(Event.timestamp.desc()).offset(skip).limit(limit).all()
    return events

@router.get("/{event_id}", response_model=EventResponse)
async def read_event(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific event by ID"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Check permissions
    if current_user.role != "admin" and event.camera.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return event

@router.post("/", response_model=EventResponse)
async def create_event(
    event: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new event"""
    # Verify camera ownership
    camera = db.query(Camera).filter(Camera.id == event.camera_id).first()
    if camera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    if current_user.role != "admin" and camera.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Verify vehicle ownership if provided
    if event.vehicle_id:
        vehicle = db.query(DetectedVehicle).filter(DetectedVehicle.id == event.vehicle_id).first()
        if vehicle is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle not found"
            )
        
        if current_user.role != "admin" and vehicle.camera.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    # Verify zone ownership if provided
    if event.zone_id:
        zone = db.query(Zone).filter(Zone.id == event.zone_id).first()
        if zone is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Zone not found"
            )
        
        if current_user.role != "admin" and zone.camera.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    db_event = Event(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: UUID,
    event: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update an event"""
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if db_event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Check permissions
    if current_user.role != "admin" and db_event.camera.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Update fields
    update_data = event.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_event, field, value)
    
    db.commit()
    db.refresh(db_event)
    return db_event

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an event"""
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if db_event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Check permissions
    if current_user.role != "admin" and db_event.camera.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    db.delete(db_event)
    db.commit()
    return None

@router.get("/recent", response_model=List[EventResponse])
async def get_recent_events(
    hours: int = 24,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get recent events from the last N hours"""
    from datetime import datetime, timedelta
    since = datetime.now() - timedelta(hours=hours)
    
    query = db.query(Event).filter(Event.timestamp >= since)
    
    # Filter by user's cameras unless admin
    if current_user.role != "admin":
        query = query.join(Event.camera).filter(Camera.owner_id == current_user.id)
    
    events = query.order_by(Event.timestamp.desc()).all()
    return events