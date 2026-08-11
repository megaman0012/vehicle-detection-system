from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from models.base import Base

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)
    rtsp_url = Column(String, nullable=False)
    username = Column(String)  # For camera authentication
    password = Column(String)  # For camera authentication
    location = Column(String)
    is_active = Column(Boolean, default=True)
    fps = Column(Integer, default=30)
    width = Column(Integer, default=1920)
    height = Column(Integer, default=1080)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    owner = relationship("User", back_populates="cameras")
    zones = relationship("Zone", back_populates="camera")
    events = relationship("Event", back_populates="camera")
