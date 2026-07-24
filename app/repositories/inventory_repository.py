"""Repository for InventoryLog database operations."""
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import InventoryLog


class InventoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_logs_for_product(self, product_id: int, limit: int = 50) -> List[InventoryLog]:
        result = await self.db.execute(
            select(InventoryLog)
            .where(InventoryLog.product_id == product_id)
            .order_by(InventoryLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, log: InventoryLog) -> InventoryLog:
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log
