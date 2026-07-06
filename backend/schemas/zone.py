from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ZoneBase(BaseModel):
    name: str
    description: Optional[str] = None
    coordinates: List[List[int]]  # List of [x, y] points
    is_active: Optional[bool] = True

class ZoneCreate(ZoneBase):
    camera_id: int

class ZoneUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    coordinates: Optional[List[List[int]]] = None
    is_active: Optional[bool] = None

class ZoneInDBBase(ZoneBase):
    id: int
    camera_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class ZoneInDB(ZoneInDBBase):
    pass

class ZoneResponse(ZoneInDBBase):
    pass