from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
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

class EventCreate(EventBase):
    vehicle_id: Optional[int] = None
    zone_id: Optional[int] = None
    camera_id: int
    user_id: Optional[int] = None
    metadata: Optional[Dict[Any, Any]] = None

class EventUpdate(BaseModel):
    event_type: Optional[EventType] = None
    description: Optional[str] = None
    metadata: Optional[Dict[Any, Any]] = None

class EventInDBBase(EventBase):
    id: int
    timestamp: datetime
    vehicle_id: Optional[int] = None
    zone_id: Optional[int] = None
    camera_id: int
    user_id: Optional[int] = None
    metadata: Optional[Dict[Any, Any]] = None

    class Config:
        orm_mode = True

class EventInDB(EventInDBBase):
    pass

class EventResponse(EventInDBBase):
    pass