from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class SystemConfigBase(BaseModel):
    key: str
    value: Optional[Any] = None
    description: Optional[str] = None
    is_active: Optional[bool] = True
    data_type: Optional[str] = "string"

class SystemConfigCreate(SystemConfigBase):
    pass

class SystemConfigUpdate(BaseModel):
    value: Optional[Any] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    data_type: Optional[str] = None

class SystemConfigInDBBase(SystemConfigBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class SystemConfigInDB(SystemConfigInDBBase):
    pass

class SystemConfigResponse(SystemConfigInDBBase):
    pass