"""Pydantic schemas for Product endpoints."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.category import CategoryOut


class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    brand: Optional[str] = Field(None, max_length=100)
    price: Decimal = Field(..., gt=0, decimal_places=2)
    discount_price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    color: Optional[str] = Field(None, max_length=50)
    gauge: Optional[str] = Field(None, max_length=20)
    length: Optional[float] = Field(None, gt=0)
    width: Optional[float] = Field(None, gt=0)
    profile: Optional[str] = Field(None, max_length=50)
    stock_quantity: int = Field(0, ge=0)
    low_stock_threshold: int = Field(10, ge=0)
    image_url: Optional[str] = Field(None, max_length=500)
    is_active: bool = True
    category_id: int

    @field_validator("discount_price")
    @classmethod
    def discount_less_than_price(cls, v, info):
        if v is not None and "price" in info.data and v >= info.data["price"]:
            raise ValueError("discount_price must be less than price")
        return v


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    discount_price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    color: Optional[str] = None
    gauge: Optional[str] = None
    length: Optional[float] = Field(None, gt=0)
    width: Optional[float] = Field(None, gt=0)
    profile: Optional[str] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    low_stock_threshold: Optional[int] = Field(None, ge=0)
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
    category_id: Optional[int] = None


class ProductOut(ProductBase):
    id: int
    category: Optional[CategoryOut] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductListOut(BaseModel):
    id: int
    name: str
    price: Decimal
    discount_price: Optional[Decimal] = None
    color: Optional[str] = None
    gauge: Optional[str] = None
    stock_quantity: int
    is_active: bool
    image_url: Optional[str] = None
    category_id: int

    model_config = {"from_attributes": True}
