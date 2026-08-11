from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Float, Interval
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from datetime import timedelta
import uuid
import enum
from models.base import Base

class VehicleType(str, enum.Enum):
    CAR = "car"
    MOTORCYCLE = "motorcycle"
    TRUCK = "truck"
    BUS = "bus"
    UNKNOWN = "unknown"

class DetectedVehicle(Base):
    __tablename__ = "detected_vehicles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    vehicle_id = Column(String, unique=True, nullable=False, index=True)  # Tracking ID from ByteTrack
    camera_id = Column(UUID(as_uuid=True), ForeignKey("cameras.id"), nullable=True)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("parking_zones.id"), nullable=True)
    license_plate = Column(String, nullable=True)
    vehicle_type = Column(String, default=VehicleType.UNKNOWN.value)
    confidence = Column(Float, default=0.0)
    bbox = Column(JSONB, nullable=True)
    first_seen = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    is_parked = Column(Boolean, default=False)
    park_start_time = Column(DateTime(timezone=True), nullable=True)
    total_park_time = Column(Interval, default=timedelta(0))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    zone = relationship("Zone")
    camera = relationship("Camera")
    events = relationship("Event", back_populates="vehicle")
