"""Pydantic schemas for Product endpoints — upgraded with price range and image gallery."""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.category import CategoryOut


# ── Product Image Schemas ─────────────────────────────────────────────────────

class ProductImageBase(BaseModel):
    image_url: str = Field(..., max_length=500)
    is_primary: bool = False
    display_order: int = 0
    alt_text: Optional[str] = Field(None, max_length=200)


class ProductImageCreate(ProductImageBase):
    pass


class ProductImageOut(ProductImageBase):
    id: int
    product_id: int

    model_config = {"from_attributes": True}


# ── Product Schemas ───────────────────────────────────────────────────────────

class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    slug: Optional[str] = Field(None, max_length=220)
    description: Optional[str] = None

    # Classification
    brand: Optional[str] = Field(None, max_length=100)
    product_type: Optional[str] = Field(None, max_length=100)
    material: Optional[str] = Field(None, max_length=100)
    finish: Optional[str] = Field(None, max_length=100)
    profile: Optional[str] = Field(None, max_length=50)

    # Physical specs
    gauge: Optional[str] = Field(None, max_length=20)
    length: Optional[float] = Field(None, gt=0)
    width: Optional[float] = Field(None, gt=0)
    color: Optional[str] = Field(None, max_length=50)
    unit: Optional[str] = Field("piece", max_length=20)

    # Pricing — range-based
    price_from: Decimal = Field(..., gt=0, decimal_places=2)
    price_to: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    discount_price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)

    # Inventory
    stock_quantity: int = Field(0, ge=0)
    minimum_order_quantity: int = Field(1, ge=1)
    low_stock_threshold: int = Field(10, ge=0)

    # Status
    is_featured: bool = False
    is_available: bool = True
    is_active: bool = True

    # Legacy single image
    image_url: Optional[str] = Field(None, max_length=500)

    category_id: int

    @field_validator("price_to")
    @classmethod
    def price_to_gte_price_from(cls, v, info):
        if v is not None and "price_from" in info.data and v < info.data["price_from"]:
            raise ValueError("price_to must be >= price_from")
        return v

    @field_validator("discount_price")
    @classmethod
    def discount_less_than_price_from(cls, v, info):
        if v is not None and "price_from" in info.data and v >= info.data["price_from"]:
            raise ValueError("discount_price must be less than price_from")
        return v


class ProductCreate(ProductBase):
    images: Optional[List[ProductImageCreate]] = []


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    slug: Optional[str] = Field(None, max_length=220)
    description: Optional[str] = None
    brand: Optional[str] = None
    product_type: Optional[str] = None
    material: Optional[str] = None
    finish: Optional[str] = None
    profile: Optional[str] = None
    gauge: Optional[str] = None
    length: Optional[float] = Field(None, gt=0)
    width: Optional[float] = Field(None, gt=0)
    color: Optional[str] = None
    unit: Optional[str] = None
    price_from: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    price_to: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    discount_price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    stock_quantity: Optional[int] = Field(None, ge=0)
    minimum_order_quantity: Optional[int] = Field(None, ge=1)
    low_stock_threshold: Optional[int] = Field(None, ge=0)
    is_featured: Optional[bool] = None
    is_available: Optional[bool] = None
    is_active: Optional[bool] = None
    image_url: Optional[str] = None
    category_id: Optional[int] = None


class ProductOut(ProductBase):
    id: int
    category: Optional[CategoryOut] = None
    images: List[ProductImageOut] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductListOut(BaseModel):
    id: int
    name: str
    slug: Optional[str] = None
    price_from: Decimal
    price_to: Optional[Decimal] = None
    discount_price: Optional[Decimal] = None
    color: Optional[str] = None
    gauge: Optional[str] = None
    stock_quantity: int
    is_active: bool
    is_featured: bool
    is_available: bool
    image_url: Optional[str] = None
    images: List[ProductImageOut] = []
    category_id: int

    model_config = {"from_attributes": True}
