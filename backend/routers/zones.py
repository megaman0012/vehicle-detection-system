from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models.zone import Zone
from schemas.zone import ZoneCreate, ZoneUpdate, ZoneResponse
from utils.auth import get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[ZoneResponse])
async def read_zones(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all zones"""
    # Users can only see zones from their own cameras unless they are admin
    if current_user.role != "admin":
        zones = db.query(Zone).join(Zone.camera).filter(Camera.owner_id == current_user.id).offset(skip).limit(limit).all()
    else:
        zones = db.query(Zone).offset(skip).limit(limit).all()
    return zones

@router.get("/{zone_id}", response_model=ZoneResponse)
async def read_zone(
    zone_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific zone by ID"""
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if zone is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zone not found"
        )
    
    # Check permissions
    if current_user.role != "admin" and zone.camera.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return zone

@router.post("/", response_model=ZoneResponse)
async def create_zone(
    zone: ZoneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new zone"""
    # Verify camera ownership
    camera = db.query(Camera).filter(Camera.id == zone.camera_id).first()
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
    
    db_zone = Zone(**zone.dict())
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    return db_zone

@router.put("/{zone_id}", response_model=ZoneResponse)
async def update_zone(
    zone_id: int,
    zone: ZoneUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a zone"""
    db_zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if db_zone is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zone not found"
        )
    
    # Check permissions
    if current_user.role != "admin" and db_zone.camera.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Update fields
    update_data = zone.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_zone, field, value)
    
    db.commit()
    db.refresh(db_zone)
    return db_zone

@router.delete("/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_zone(
    zone_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a zone"""
    db_zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if db_zone is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zone not found"
        )
    
    # Check permissions
    if current_user.role != "admin" and db_zone.camera.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    db.delete(db_zone)
    db.commit()
    return None