from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
import enum
from models.base import Base

class EventType(str, enum.Enum):
    VEHICLE_PARKED = "vehicle_parked"
    VEHICLE_LEFT = "vehicle_left"
    PLATE_DETECTED = "plate_detected"
    CAMERA_OFFLINE = "camera_offline"
    SYSTEM_ALERT = "system_alert"

class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    camera_id = Column(UUID(as_uuid=True), ForeignKey("cameras.id"), nullable=True)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("parking_zones.id"), nullable=True)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("detected_vehicles.id"), nullable=True)
    event_type = Column(String, nullable=False)
    description = Column(Text)
    license_plate = Column(String, nullable=True)
    # 'metadata' is a reserved name in SQLAlchemy declarative, so the Python
    # attribute is 'meta' while the DB column keeps the name 'metadata'.
    meta = Column("metadata", JSONB, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    vehicle = relationship("DetectedVehicle", back_populates="events")
    zone = relationship("Zone", back_populates="events")
    camera = relationship("Camera", back_populates="events")
