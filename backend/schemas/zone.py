from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class ZoneBase(BaseModel):
    name: str
    coordinates: List[List[int]]  # List of [x, y] points
    is_active: Optional[bool] = True

class ZoneCreate(ZoneBase):
    camera_id: UUID

class ZoneUpdate(BaseModel):
    name: Optional[str] = None
    coordinates: Optional[List[List[int]]] = None
    is_active: Optional[bool] = None

class ZoneInDBBase(ZoneBase):
    id: UUID
    camera_id: Optional[UUID] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ZoneInDB(ZoneInDBBase):
    pass

class ZoneResponse(ZoneInDBBase):
    pass
