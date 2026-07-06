from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime

class CameraBase(BaseModel):
    name: str
    description: Optional[str] = None
    rtsp_url: str
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = True
    location: Optional[str] = None

class CameraCreate(CameraBase):
    pass

class CameraUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    rtsp_url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    location: Optional[str] = None

class CameraInDBBase(CameraBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    owner_id: int

    class Config:
        orm_mode = True

class CameraInDB(CameraInDBBase):
    pass

class CameraResponse(CameraInDBBase):
    pass