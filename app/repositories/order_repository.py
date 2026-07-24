"""Repository for Order database operations."""
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem


class OrderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, order_id: int) -> Optional[Order]:
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_by_customer(self, customer_id: int, skip: int = 0, limit: int = 50) -> List[Order]:
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.customer_id == customer_id)
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_all(self, skip: int = 0, limit: int = 50, status: Optional[str] = None) -> List[Order]:
        query = select(Order).options(selectinload(Order.items)).order_by(Order.created_at.desc())
        if status:
            query = query.where(Order.status == status)
        result = await self.db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(Order))
        return result.scalar_one()

    async def total_revenue(self) -> Decimal:
        result = await self.db.execute(
            select(func.sum(Order.total_amount)).where(Order.status == "completed")
        )
        val = result.scalar_one()
        return val or Decimal("0.00")

    async def count_by_status(self, status: str) -> int:
        result = await self.db.execute(
            select(func.count()).where(Order.status == status)
        )
        return result.scalar_one()

    async def create(self, order: Order) -> Order:
        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)
        return await self.get_by_id(order.id)

    async def update(self, order: Order) -> Order:
        await self.db.commit()
        await self.db.refresh(order)
        return await self.get_by_id(order.id)
