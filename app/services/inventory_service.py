"""Inventory management service."""
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import InventoryLog
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.inventory import InventoryUpdate


class InventoryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.product_repo = ProductRepository(db)
        self.inv_repo = InventoryRepository(db)

    async def update_stock(
        self,
        product_id: int,
        data: InventoryUpdate,
        performed_by: int,
    ):
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        new_qty = product.stock_quantity + data.change
        if new_qty < 0:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock. Current: {product.stock_quantity}, requested change: {data.change}",
            )

        product.stock_quantity = new_qty
        await self.product_repo.update(product)

        log = InventoryLog(
            product_id=product_id,
            change=data.change,
            reason=data.reason,
            note=data.note,
            performed_by=performed_by,
        )
        return await self.inv_repo.create(log)
