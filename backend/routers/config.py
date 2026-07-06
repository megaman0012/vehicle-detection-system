from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database import get_db
from backend.models.config import SystemConfig
from backend.schemas.config import SystemConfigCreate, SystemConfigUpdate, SystemConfigResponse
from backend.utils.auth import get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[SystemConfigResponse])
async def read_configs(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all system configurations"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    query = db.query(SystemConfig)
    if active_only:
        query = query.filter(SystemConfig.is_active == True)
    
    configs = query.offset(skip).limit(limit).all()
    return configs

@router.get("/{config_id}", response_model=SystemConfigResponse)
async def read_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific configuration by ID"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    config = db.query(SystemConfig).filter(SystemConfig.id == config_id).first()
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )
    return config

@router.get("/by-key/{key}", response_model=SystemConfigResponse)
async def read_config_by_key(
    key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a configuration by key"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )
    return config

@router.post("/", response_model=SystemConfigResponse)
async def create_config(
    config: SystemConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new system configuration"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Check if key already exists
    db_config = db.query(SystemConfig).filter(SystemConfig.key == config.key).first()
    if db_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Configuration key already exists"
        )
    
    db_config = SystemConfig(**config.dict())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config

@router.put("/{config_id}", response_model=SystemConfigResponse)
async def update_config(
    config_id: int,
    config: SystemConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a system configuration"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    db_config = db.query(SystemConfig).filter(SystemConfig.id == config_id).first()
    if db_config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )
    
    # Update fields
    update_data = config.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_config, field, value)
    
    db.commit()
    db.refresh(db_config)
    return db_config

@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a system configuration"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    db_config = db.query(SystemConfig).filter(SystemConfig.id == config_id).first()
    if db_config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )
    
    db.delete(db_config)
    db.commit()
    return None

@router.post("/initialize-defaults")
async def initialize_default_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Initialize default system configurations"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    default_configs = [
        {
            "key": "parking_time_threshold",
            "value": "300",  # 5 minutes in seconds
            "description": "Time in seconds to consider a vehicle as parked",
            "data_type": "integer"
        },
        {
            "key": "working_hours_start",
            "value": "08:00",
            "description": "Start of working hours (HH:MM format)",
            "data_type": "string"
        },
        {
            "key": "working_hours_end",
            "value": "18:00",
            "description": "End of working hours (HH:MM format)",
            "data_type": "string"
        },
        {
            "key": "whatsapp_enabled",
            "value": "true",
            "description": "Enable WhatsApp notifications",
            "data_type": "boolean"
        },
        {
            "key": "default_whatsapp_numbers",
            "value": "[]",
            "description": "Default WhatsApp numbers for notifications",
            "data_type": "json"
        }
    ]
    
    created_configs = []
    for config_data in default_configs:
        # Check if config already exists
        existing = db.query(SystemConfig).filter(SystemConfig.key == config_data["key"]).first()
        if not existing:
            config = SystemConfig(**config_data)
            db.add(config)
            created_configs.append(config)
    
    if created_configs:
        db.commit()
        for config in created_configs:
            db.refresh(config)
    
    return {"message": f"Initialized {len(created_configs)} default configurations"}