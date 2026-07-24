"""Order router: customer order creation and admin order management."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_admin, get_current_user, get_db
from app.repositories.order_repository import OrderRepository
from app.schemas.order import OrderCreate, OrderOut, OrderStatusUpdate
from app.services.order_service import OrderService

router = APIRouter(tags=["Orders"])


# ── Customer ─────────────────────────────────────────────────────────────────

@router.post("/orders", response_model=OrderOut, status_code=201)
async def create_order(
    data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Place a new order (authenticated customers)."""
    service = OrderService(db)
    return await service.create_order(customer_id=current_user.id, data=data)


@router.get("/orders/my-orders", response_model=List[OrderOut])
async def my_orders(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List the current customer's orders."""
    repo = OrderRepository(db)
    return await repo.get_by_customer(current_user.id, skip=skip, limit=limit)


@router.get("/orders/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get a specific order (owner or admin)."""
    repo = OrderRepository(db)
    order = await repo.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.customer_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return order


# ── Admin ────────────────────────────────────────────────────────────────────

@router.get("/admin/orders", response_model=List[OrderOut])
async def list_all_orders(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = Query(None, description="Filter by order status"),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    """List all orders with optional status filter (admin only)."""
    repo = OrderRepository(db)
    return await repo.get_all(skip=skip, limit=limit, status=status)


@router.put("/admin/orders/{order_id}/status", response_model=OrderOut)
async def update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    """Update an order's status (admin only)."""
    service = OrderService(db)
    return await service.update_status(order_id, data)
