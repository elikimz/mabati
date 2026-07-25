"""Pydantic schemas for orders and variation-aware order items."""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class OrderItemCreate(BaseModel):
    product_id: int
    variation_id: Optional[int] = None
    quantity: int = Field(..., gt=0)


class OrderCreate(BaseModel):
    items: List[OrderItemCreate] = Field(..., min_length=1)
    shipping_address: Optional[str] = None
    notes: Optional[str] = None


class OrderItemOut(BaseModel):
    id: int
    product_id: int
    variation_id: Optional[int] = None
    quantity: int
    unit_price: Decimal
    variation_snapshot: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: int
    customer_id: int
    status: str
    total_amount: Decimal
    shipping_address: Optional[str] = None
    notes: Optional[str] = None
    items: List[OrderItemOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderStatusUpdate(BaseModel):
    status: Literal["pending", "confirmed", "processing", "completed", "cancelled"]
