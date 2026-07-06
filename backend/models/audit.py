"""
Audit Log Model for Vehicle Detection System
"""
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)  # e.g., "CREATE_USER", "UPDATE_CAMERA"
    resource_type = Column(String(50), nullable=False, index=True)  # e.g., "user", "camera", "vehicle"
    resource_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    details = Column(JSONB, nullable=True)  # Additional context about the action
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Optional: Define relationships if needed
    # user = relationship("User", foreign_keys=[user_id])
    # resource = relationship("User", foreign_keys=[resource_id])