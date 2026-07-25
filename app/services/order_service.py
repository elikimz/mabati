"""Order management service with variation-aware price snapshots."""
from decimal import Decimal
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderItem
from app.models.product import ProductVariation
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.order import OrderCreate, OrderStatusUpdate


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.order_repo = OrderRepository(db)
        self.product_repo = ProductRepository(db)

    @staticmethod
    def _variation_snapshot(variation: ProductVariation) -> Dict[str, Any]:
        label = variation.name or " / ".join(
            part
            for part in [
                f"Gauge {variation.gauge}" if variation.gauge else None,
                variation.size_label,
                variation.color,
            ]
            if part
        ) or "Standard option"
        return {
            "label": label,
            "sku": variation.sku,
            "gauge": variation.gauge,
            "size_label": variation.size_label,
            "length": variation.length,
            "width": variation.width,
            "color": variation.color,
            "unit": variation.unit,
            "specifications": variation.specifications or {},
        }

    @staticmethod
    def _select_variation(product, variation_id: Optional[int]) -> Optional[ProductVariation]:
        active_variations = [
            variation
            for variation in product.variations
            if variation.is_active and variation.is_available
        ]

        if variation_id is not None:
            selected = next((item for item in product.variations if item.id == variation_id), None)
            if not selected:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Variation {variation_id} does not belong to '{product.name}'",
                )
            if not selected.is_active or not selected.is_available:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"The selected variation for '{product.name}' is not available",
                )
            return selected

        # Product-only requests remain supported when there is exactly one viable
        # option, which includes every legacy product backfilled by the migration.
        if len(active_variations) == 1:
            return active_variations[0]
        if len(active_variations) > 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Select a variation for '{product.name}' before ordering",
            )
        return None

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
            if not product.is_active or not product.is_available:
                raise HTTPException(
                    status_code=400,
                    detail=f"Product '{product.name}' is not available",
                )
            if product.stock_quantity < item_data.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for '{product.name}'. Available: {product.stock_quantity}",
                )

            variation = self._select_variation(product, item_data.variation_id)
            if variation is not None:
                unit_price = Decimal(
                    variation.discount_price
                    if variation.discount_price is not None
                    else variation.price
                )
                variation_snapshot = self._variation_snapshot(variation)
            else:
                # Covers a pre-migration product only if it has no stored options.
                unit_price = Decimal(product.discount_price or product.price_from)
                variation_snapshot = None

            order_items.append(
                OrderItem(
                    product_id=product.id,
                    variation_id=variation.id if variation else None,
                    quantity=item_data.quantity,
                    unit_price=unit_price,
                    variation_snapshot=variation_snapshot,
                )
            )
            total += unit_price * item_data.quantity

            # Preserve existing product-level inventory semantics. All stock updates
            # participate in the single transaction committed when the order is saved.
            product.stock_quantity -= item_data.quantity

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

        # Restore product-level stock if cancelling.
        if data.status == "cancelled" and order.status != "cancelled":
            for item in order.items:
                product = await self.product_repo.get_by_id(item.product_id)
                if product:
                    product.stock_quantity += item.quantity

        order.status = data.status
        return await self.order_repo.update(order)
