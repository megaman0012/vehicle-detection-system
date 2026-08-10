from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from models.base import Base
import enum

class VehicleType(str, enum.Enum):
    CAR = "car"
    MOTORCYCLE = "motorcycle"
    TRUCK = "truck"
    BUS = "bus"
    UNKNOWN = "unknown"

class DetectedVehicle(Base):
    __tablename__ = "detected_vehicles"

    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(Integer, nullable=False, index=True)  # ID from ByteTrack
    vehicle_type = Column(Enum(VehicleType), default=VehicleType.UNKNOWN)
    confidence = Column(String)  # Confidence score from YOLO
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    first_seen_at = Column(DateTime(timezone=True), server_default=func.now())
    is_parked = Column(Boolean, default=False)
    parked_since = Column(DateTime(timezone=True), nullable=True)
    license_plate = Column(String, nullable=True)
    plate_confidence = Column(String, nullable=True)  # Confidence from OCR
    image_path = Column(String, nullable=True)  # Path to saved image
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)

    # Relationships
    zone = relationship("Zone")
    camera = relationship("Camera")
    events = relationship("Event", back_populates="vehicle")