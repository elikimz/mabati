from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class GalleryBase(BaseModel):
    title: str
    description: Optional[str] = None
    image_url: str
    display_order: int = 0
    is_active: bool = True
    category: Optional[str] = None

class GalleryCreate(GalleryBase):
    pass

class GalleryUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None
    category: Optional[str] = None

class GalleryOut(GalleryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
