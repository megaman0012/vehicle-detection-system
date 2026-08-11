from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

class EventType(str, Enum):
    VEHICLE_PARKED = "vehicle_parked"
    VEHICLE_LEFT = "vehicle_left"
    PLATE_DETECTED = "plate_detected"
    CAMERA_OFFLINE = "camera_offline"
    SYSTEM_ALERT = "system_alert"

class EventBase(BaseModel):
    event_type: EventType
    description: Optional[str] = None
    license_plate: Optional[str] = None

class EventCreate(EventBase):
    vehicle_id: Optional[UUID] = None
    zone_id: Optional[UUID] = None
    camera_id: UUID
    meta: Optional[Dict[Any, Any]] = None

class EventUpdate(BaseModel):
    event_type: Optional[EventType] = None
    description: Optional[str] = None
    license_plate: Optional[str] = None
    meta: Optional[Dict[Any, Any]] = None

class EventInDBBase(EventBase):
    id: UUID
    timestamp: datetime
    vehicle_id: Optional[UUID] = None
    zone_id: Optional[UUID] = None
    camera_id: Optional[UUID] = None
    meta: Optional[Dict[Any, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class EventInDB(EventInDBBase):
    pass

class EventResponse(EventInDBBase):
    pass
