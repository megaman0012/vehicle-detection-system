from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from models.base import Base
import enum

class EventType(str, enum.Enum):
    VEHICLE_PARKED = "vehicle_parked"
    VEHICLE_LEFT = "vehicle_left"
    PLATE_DETECTED = "plate_detected"
    CAMERA_OFFLINE = "camera_offline"
    SYSTEM_ALERT = "system_alert"

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(Enum(EventType), nullable=False)
    description = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Foreign keys
    vehicle_id = Column(Integer, ForeignKey("detected_vehicles.id"), nullable=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Who triggered/resolved
    
    # Additional data
    event_metadata = Column(Text, nullable=True)  # JSON string for additional data
    
    # Relationships
    vehicle = relationship("DetectedVehicle", back_populates="events")
    zone = relationship("Zone", back_populates="events")
    camera = relationship("Camera", back_populates="events")
    user = relationship("User", back_populates="events")

    def get_metadata(self):
        """Return metadata as dict"""
        import json
        return json.loads(self.event_metadata) if self.event_metadata else {}

    def set_metadata(self, data):
        """Set metadata from dict"""
        import json
        self.event_metadata = json.dumps(data)