"""Inventory router: stock management and low-stock alerts."""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_admin, get_current_staff_or_admin, get_db
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.inventory import InventoryLogOut, InventoryUpdate, LowStockItem
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/admin/inventory", tags=["Inventory (Admin)"])


@router.get("/", response_model=List[LowStockItem])
async def get_inventory_overview(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_staff_or_admin),
):
    """List all products with low stock (at or below threshold)."""
    repo = ProductRepository(db)
    return await repo.get_low_stock()


@router.post("/{product_id}/adjust", response_model=InventoryLogOut)
async def adjust_stock(
    product_id: int,
    data: InventoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_staff_or_admin),
):
    """
    Adjust stock for a product.

    - Positive **change** = restock
    - Negative **change** = removal / sale adjustment
    """
    service = InventoryService(db)
    return await service.update_stock(product_id, data, performed_by=current_user.id)


@router.get("/{product_id}/logs", response_model=List[InventoryLogOut])
async def get_inventory_logs(
    product_id: int,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_staff_or_admin),
):
    """Get inventory change history for a specific product."""
    repo = InventoryRepository(db)
    return await repo.get_logs_for_product(product_id, limit=limit)
