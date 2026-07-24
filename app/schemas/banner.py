"""Pydantic schemas for landing page banners."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class BannerBase(BaseModel):
    title: Optional[str] = Field(None, max_length=100)
    subtitle: Optional[str] = Field(None, max_length=200)
    image_url: str = Field(..., max_length=500)
    link_url: Optional[str] = Field(None, max_length=200)
    display_order: int = 0
    is_active: bool = True
    location: str = Field("hero", max_length=50)

class BannerCreate(BannerBase):
    pass

class BannerUpdate(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    image_url: Optional[str] = None
    link_url: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None
    location: Optional[str] = None

class BannerOut(BannerBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
