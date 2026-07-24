"""Pydantic schemas for Inventory endpoints."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class InventoryUpdate(BaseModel):
    change: int = Field(..., description="Positive to add stock, negative to remove")
    reason: Optional[str] = Field(None, max_length=100)
    note: Optional[str] = None


class InventoryLogOut(BaseModel):
    id: int
    product_id: int
    change: int
    reason: Optional[str] = None
    note: Optional[str] = None
    performed_by: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LowStockItem(BaseModel):
    id: int
    name: str
    stock_quantity: int
    low_stock_threshold: int

    model_config = {"from_attributes": True}
