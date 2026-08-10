from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models.camera import Camera
from models.user import User
from schemas.camera import CameraCreate, CameraUpdate, CameraResponse
from utils.auth import get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[CameraResponse])
async def read_cameras(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all cameras"""
    # Users can only see their own cameras unless they are admin
    if current_user.role != "admin":
        cameras = db.query(Camera).filter(Camera.owner_id == current_user.id).offset(skip).limit(limit).all()
    else:
        cameras = db.query(Camera).offset(skip).limit(limit).all()
    return cameras

@router.get("/{camera_id}", response_model=CameraResponse)
async def read_camera(
    camera_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific camera by ID"""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if camera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    # Check permissions
    if current_user.role != "admin" and camera.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return camera

@router.post("/", response_model=CameraResponse)
async def create_camera(
    camera: CameraCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new camera"""
    db_camera = Camera(
        **camera.dict(),
        owner_id=current_user.id
    )
    
    db.add(db_camera)
    db.commit()
    db.refresh(db_camera)
    return db_camera

@router.put("/{camera_id}", response_model=CameraResponse)
async def update_camera(
    camera_id: int,
    camera: CameraUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a camera"""
    db_camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if db_camera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    # Check permissions
    if current_user.role != "admin" and db_camera.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Update fields
    update_data = camera.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_camera, field, value)
    
    db.commit()
    db.refresh(db_camera)
    return db_camera

@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(
    camera_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a camera"""
    db_camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if db_camera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    # Check permissions
    if current_user.role != "admin" and db_camera.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    db.delete(db_camera)
    db.commit()
    return None