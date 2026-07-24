"""Order management service."""
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderItem
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.order import OrderCreate, OrderStatusUpdate


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.order_repo = OrderRepository(db)
        self.product_repo = ProductRepository(db)

    async def create_order(self, customer_id: int, data: OrderCreate) -> Order:
        order_items = []
        total = Decimal("0.00")

        for item_data in data.items:
            product = await self.product_repo.get_by_id(item_data.product_id)
            if not product:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product {item_data.product_id} not found",
                )
            if not product.is_active:
                raise HTTPException(
                    status_code=400,
                    detail=f"Product '{product.name}' is not available",
                )
            if product.stock_quantity < item_data.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for '{product.name}'. Available: {product.stock_quantity}",
                )

            unit_price = product.discount_price or product.price
            order_items.append(
                OrderItem(
                    product_id=product.id,
                    quantity=item_data.quantity,
                    unit_price=unit_price,
                )
            )
            total += unit_price * item_data.quantity

            # Deduct stock
            product.stock_quantity -= item_data.quantity
            await self.product_repo.update(product)

        order = Order(
            customer_id=customer_id,
            total_amount=total,
            shipping_address=data.shipping_address,
            notes=data.notes,
            items=order_items,
        )
        return await self.order_repo.create(order)

    async def update_status(self, order_id: int, data: OrderStatusUpdate) -> Order:
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Restore stock if cancelling
        if data.status == "cancelled" and order.status != "cancelled":
            for item in order.items:
                product = await self.product_repo.get_by_id(item.product_id)
                if product:
                    product.stock_quantity += item.quantity
                    await self.product_repo.update(product)

        order.status = data.status
        return await self.order_repo.update(order)
