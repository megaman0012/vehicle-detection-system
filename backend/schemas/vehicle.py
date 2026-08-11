from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

class VehicleType(str, Enum):
    CAR = "car"
    MOTORCYCLE = "motorcycle"
    TRUCK = "truck"
    BUS = "bus"
    UNKNOWN = "unknown"

class DetectedVehicleBase(BaseModel):
    vehicle_id: str
    vehicle_type: Optional[VehicleType] = VehicleType.UNKNOWN
    confidence: Optional[float] = 0.0
    is_parked: Optional[bool] = False
    license_plate: Optional[str] = None

class DetectedVehicleCreate(DetectedVehicleBase):
    camera_id: UUID
    zone_id: Optional[UUID] = None
    bbox: Optional[Any] = None

class DetectedVehicleUpdate(BaseModel):
    vehicle_type: Optional[VehicleType] = None
    confidence: Optional[float] = None
    is_parked: Optional[bool] = None
    license_plate: Optional[str] = None
    bbox: Optional[Any] = None
    zone_id: Optional[UUID] = None
    park_start_time: Optional[datetime] = None

class DetectedVehicleInDBBase(DetectedVehicleBase):
    id: UUID
    camera_id: Optional[UUID] = None
    zone_id: Optional[UUID] = None
    bbox: Optional[Any] = None
    first_seen: datetime
    last_seen: datetime
    park_start_time: Optional[datetime] = None
    total_park_time: Optional[Any] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class DetectedVehicleInDB(DetectedVehicleInDBBase):
    pass

class DetectedVehicleResponse(DetectedVehicleInDBBase):
    pass
