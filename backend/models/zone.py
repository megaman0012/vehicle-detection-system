from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import json
from backend.models.base import Base

class Zone(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    # Store polygon coordinates as JSON: [[x1,y1], [x2,y2], ...]
    coordinates = Column(Text, nullable=False)  # JSON string of polygon points
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    camera = relationship("Camera", back_populates="zones")
    events = relationship("Event", back_populates="zone")

    def get_coordinates(self):
        """Return coordinates as list of lists"""
        import json
        return json.loads(self.coordinates) if self.coordinates else []

    def set_coordinates(self, coords):
        """Set coordinates from list of lists"""
        import json
        self.coordinates = json.dumps(coords)