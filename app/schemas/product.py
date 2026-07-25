"""Pydantic schemas for product, variation, and product-image endpoints."""
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator

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


# ── Product Variation Schemas ─────────────────────────────────────────────────

class ProductVariationBase(BaseModel):
    """Fields that make one product option independently sellable and priced."""

    name: Optional[str] = Field(None, max_length=120)
    sku: Optional[str] = Field(None, max_length=100)
    gauge: Optional[str] = Field(None, max_length=20)
    size_label: Optional[str] = Field(None, max_length=100)
    length: Optional[float] = Field(None, gt=0)
    width: Optional[float] = Field(None, gt=0)
    color: Optional[str] = Field(None, max_length=50)
    unit: str = Field("piece", min_length=1, max_length=20)
    price: Decimal = Field(..., gt=0, decimal_places=2)
    discount_price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    specifications: Dict[str, str] = Field(default_factory=dict)
    sort_order: int = Field(0, ge=0)
    is_available: bool = True
    is_active: bool = True

    @field_validator("specifications")
    @classmethod
    def specifications_are_clean(cls, value: Dict[str, str]) -> Dict[str, str]:
        cleaned: Dict[str, str] = {}
        for key, item in value.items():
            clean_key = key.strip()
            clean_value = item.strip()
            if not clean_key or not clean_value:
                raise ValueError("specification names and values cannot be blank")
            if len(clean_key) > 80 or len(clean_value) > 300:
                raise ValueError("specification names must be <= 80 and values <= 300 characters")
            cleaned[clean_key] = clean_value
        return cleaned

    @model_validator(mode="after")
    def discount_is_lower_than_regular_price(self):
        if self.discount_price is not None and self.discount_price >= self.price:
            raise ValueError("discount_price must be less than price")
        return self


class ProductVariationCreate(ProductVariationBase):
    pass


class ProductVariationUpsert(ProductVariationBase):
    """Create a new variation or update an existing child in a product PUT request."""

    id: Optional[int] = Field(None, gt=0)


class ProductVariationOut(ProductVariationBase):
    id: int
    product_id: int
    created_at: datetime
    updated_at: datetime

    @computed_field(return_type=Decimal)
    @property
    def effective_price(self) -> Decimal:
        """The price a customer should see and be charged for this variation."""
        return self.discount_price or self.price

    model_config = {"from_attributes": True}


# ── Product Schemas ───────────────────────────────────────────────────────────

class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    slug: Optional[str] = Field(None, max_length=220)
    description: Optional[str] = None

    # Product-family classification
    brand: Optional[str] = Field(None, max_length=100)
    product_type: Optional[str] = Field(None, max_length=100)
    material: Optional[str] = Field(None, max_length=100)
    finish: Optional[str] = Field(None, max_length=100)
    profile: Optional[str] = Field(None, max_length=50)

    # Legacy / product-level specs. Per-option specs should be placed in variations.
    gauge: Optional[str] = Field(None, max_length=20)
    length: Optional[float] = Field(None, gt=0)
    width: Optional[float] = Field(None, gt=0)
    color: Optional[str] = Field(None, max_length=50)
    unit: Optional[str] = Field("piece", max_length=20)

    # Legacy / aggregate pricing. Service maintains these from active variations.
    price_from: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    price_to: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    discount_price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)

    # Product-level inventory retained for legacy stock management
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
    def price_to_gte_price_from(cls, value, info):
        price_from = info.data.get("price_from")
        if value is not None and price_from is not None and value < price_from:
            raise ValueError("price_to must be >= price_from")
        return value

    @field_validator("discount_price")
    @classmethod
    def discount_less_than_price_from(cls, value, info):
        price_from = info.data.get("price_from")
        if value is not None and price_from is not None and value >= price_from:
            raise ValueError("discount_price must be less than price_from")
        return value


class ProductCreate(ProductBase):
    images: List[ProductImageCreate] = Field(default_factory=list)
    variations: List[ProductVariationCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def requires_a_price_source(self):
        if not self.variations and self.price_from is None:
            raise ValueError("price_from is required when no product variations are supplied")
        return self


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    slug: Optional[str] = Field(None, max_length=220)
    description: Optional[str] = None
    brand: Optional[str] = Field(None, max_length=100)
    product_type: Optional[str] = Field(None, max_length=100)
    material: Optional[str] = Field(None, max_length=100)
    finish: Optional[str] = Field(None, max_length=100)
    profile: Optional[str] = Field(None, max_length=50)
    gauge: Optional[str] = Field(None, max_length=20)
    length: Optional[float] = Field(None, gt=0)
    width: Optional[float] = Field(None, gt=0)
    color: Optional[str] = Field(None, max_length=50)
    unit: Optional[str] = Field(None, max_length=20)
    price_from: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    price_to: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    discount_price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    stock_quantity: Optional[int] = Field(None, ge=0)
    minimum_order_quantity: Optional[int] = Field(None, ge=1)
    low_stock_threshold: Optional[int] = Field(None, ge=0)
    is_featured: Optional[bool] = None
    is_available: Optional[bool] = None
    is_active: Optional[bool] = None
    image_url: Optional[str] = Field(None, max_length=500)
    category_id: Optional[int] = None
    # When supplied, this list is the complete desired set: included IDs are
    # updated, items without IDs are created, and omitted existing items are removed.
    variations: Optional[List[ProductVariationUpsert]] = None


class ProductOut(ProductBase):
    id: int
    price_from: Decimal
    category: Optional[CategoryOut] = None
    images: List[ProductImageOut] = Field(default_factory=list)
    variations: List[ProductVariationOut] = Field(default_factory=list)
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
    images: List[ProductImageOut] = Field(default_factory=list)
    variations: List[ProductVariationOut] = Field(default_factory=list)
    category_id: int

    model_config = {"from_attributes": True}
