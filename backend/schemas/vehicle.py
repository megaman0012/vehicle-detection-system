from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class VehicleType(str, Enum):
    CAR = "car"
    MOTORCYCLE = "motorcycle"
    TRUCK = "truck"
    BUS = "bus"
    UNKNOWN = "unknown"

class DetectedVehicleBase(BaseModel):
    track_id: int
    vehicle_type: Optional[VehicleType] = VehicleType.UNKNOWN
    confidence: Optional[str] = None
    is_parked: Optional[bool] = False
    license_plate: Optional[str] = None
    plate_confidence: Optional[str] = None

class DetectedVehicleCreate(DetectedVehicleBase):
    pass

class DetectedVehicleUpdate(BaseModel):
    vehicle_type: Optional[VehicleType] = None
    confidence: Optional[str] = None
    is_parked: Optional[bool] = None
    parked_since: Optional[datetime] = None
    license_plate: Optional[str] = None
    plate_confidence: Optional[str] = None
    image_path: Optional[str] = None
    zone_id: Optional[int] = None

class DetectedVehicleInDBBase(DetectedVehicleBase):
    id: int
    first_seen_at: datetime
    last_seen_at: datetime
    parked_since: Optional[datetime] = None
    is_active: bool

    class Config:
        orm_mode = True

class DetectedVehicleInDB(DetectedVehicleInDBBase):
    pass

class DetectedVehicleResponse(DetectedVehicleInDBBase):
    pass