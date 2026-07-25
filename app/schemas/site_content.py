from typing import Any, Optional
from pydantic import BaseModel
from datetime import datetime

class SiteContentBase(BaseModel):
    key: str
    value: Any
    description: Optional[str] = None

class SiteContentCreate(SiteContentBase):
    pass

class SiteContentUpdate(BaseModel):
    value: Any
    description: Optional[str] = None

class SiteContentOut(SiteContentBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True
