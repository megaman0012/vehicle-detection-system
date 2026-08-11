from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

class CameraBase(BaseModel):
    name: str
    rtsp_url: str
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = True
    location: Optional[str] = None
    fps: Optional[int] = 30
    width: Optional[int] = 1920
    height: Optional[int] = 1080

class CameraCreate(CameraBase):
    pass

class CameraUpdate(BaseModel):
    name: Optional[str] = None
    rtsp_url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    location: Optional[str] = None
    fps: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None

class CameraInDBBase(CameraBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    owner_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)

class CameraInDB(CameraInDBBase):
    pass

class CameraResponse(CameraInDBBase):
    pass
