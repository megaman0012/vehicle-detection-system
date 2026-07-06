from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.models.base import Base

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    rtsp_url = Column(String, nullable=False)
    username = Column(String)  # For camera authentication
    password = Column(String)  # For camera authentication
    is_active = Column(Boolean, default=True)
    location = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    owner_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    owner = relationship("User", back_populates="cameras")
    zones = relationship("Zone", back_populates="camera")
    events = relationship("Event", back_populates="camera")