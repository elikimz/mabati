"""Pydantic schemas for Order endpoints."""
from datetime import datetime
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)


class OrderCreate(BaseModel):
    items: List[OrderItemCreate] = Field(..., min_length=1)
    shipping_address: Optional[str] = None
    notes: Optional[str] = None


class OrderItemOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: Decimal

    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: int
    customer_id: int
    status: str
    total_amount: Decimal
    shipping_address: Optional[str] = None
    notes: Optional[str] = None
    items: List[OrderItemOut] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderStatusUpdate(BaseModel):
    status: Literal["pending", "confirmed", "processing", "completed", "cancelled"]
