"""Pydantic schemas for admin dashboard statistics."""
from decimal import Decimal
from typing import List

from pydantic import BaseModel

from app.schemas.inventory import LowStockItem


class SalesSummary(BaseModel):
    total_revenue: Decimal
    completed_orders: int
    pending_orders: int
    cancelled_orders: int


class DashboardStats(BaseModel):
    total_products: int
    total_categories: int
    total_customers: int
    total_orders: int
    sales_summary: SalesSummary
    low_stock_products: List[LowStockItem]
