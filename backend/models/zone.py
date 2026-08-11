from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from models.base import Base

class Zone(Base):
    __tablename__ = "parking_zones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    camera_id = Column(UUID(as_uuid=True), ForeignKey("cameras.id"), nullable=True)
    name = Column(String, nullable=False)
    # Store polygon coordinates as JSON: [[x1,y1], [x2,y2], ...]
    coordinates = Column(JSONB, nullable=False, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    camera = relationship("Camera", back_populates="zones")
    events = relationship("Event", back_populates="zone")
