from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
from datetime import datetime
from uuid import UUID

class SystemConfigBase(BaseModel):
    key: str
    value: Optional[Any] = None
    description: Optional[str] = None

class SystemConfigCreate(SystemConfigBase):
    pass

class SystemConfigUpdate(BaseModel):
    value: Optional[Any] = None
    description: Optional[str] = None

class SystemConfigInDBBase(SystemConfigBase):
    id: UUID
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class SystemConfigInDB(SystemConfigInDBBase):
    pass

class SystemConfigResponse(SystemConfigInDBBase):
    pass
