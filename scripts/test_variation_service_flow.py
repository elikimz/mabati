"""Exercise product variations and order snapshots against a disposable local database."""
from __future__ import annotations

import asyncio
from decimal import Decimal
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database.base import Base
import app.models  # noqa: F401  -- register ORM models
from app.models.category import Category
from app.models.user import User
from app.schemas.order import OrderCreate, OrderItemCreate
from app.schemas.product import ProductCreate, ProductUpdate, ProductVariationCreate, ProductVariationUpsert
from app.services.order_service import OrderService
from app.services.product_service import ProductService

DATABASE_PATH = Path("/tmp/mabati_variation_service_test.db")
DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_PATH}"


async def run() -> None:
    DATABASE_PATH.unlink(missing_ok=True)
    engine = create_async_engine(DATABASE_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        category = Category(name="Roofing Profiles")
        customer = User(
            name="Variation Test Customer",
            email="variation-test@example.test",
            hashed_password="not-used-in-test",
            role="customer",
        )
        session.add_all([category, customer])
        await session.commit()

        product_service = ProductService(session)
        roman_tile = await product_service.create(
            ProductCreate(
                name="Roman Tile Profile",
                category_id=category.id,
                stock_quantity=20,
                variations=[
                    ProductVariationCreate(
                        name="30 Gauge",
                        sku="ROMAN-30-TEST",
                        gauge="30 Gauge",
                        unit="MTRS",
                        price=Decimal("550.00"),
                        specifications={"Coating": "Colour coated", "Profile": "Roman Tile"},
                        sort_order=0,
                    ),
                    ProductVariationCreate(
                        name="28 Gauge",
                        sku="ROMAN-28-TEST",
                        gauge="28 Gauge",
                        unit="MTRS",
                        price=Decimal("650.00"),
                        specifications={"Coating": "Colour coated", "Profile": "Roman Tile"},
                        sort_order=1,
                    ),
                ],
            )
        )
        assert roman_tile.price_from == Decimal("550.00")
        assert roman_tile.price_to == Decimal("650.00")
        assert len(roman_tile.variations) == 2

        updated = await product_service.update(
            roman_tile.id,
            ProductUpdate(
                variations=[
                    ProductVariationUpsert(
                        id=roman_tile.variations[0].id,
                        name="30 Gauge",
                        sku="ROMAN-30-TEST",
                        gauge="30 Gauge",
                        unit="MTRS",
                        price=Decimal("570.00"),
                        specifications={"Coating": "Colour coated", "Profile": "Roman Tile"},
                        sort_order=0,
                    ),
                    ProductVariationUpsert(
                        id=roman_tile.variations[1].id,
                        name="28 Gauge",
                        sku="ROMAN-28-TEST",
                        gauge="28 Gauge",
                        unit="MTRS",
                        price=Decimal("650.00"),
                        specifications={"Coating": "Colour coated", "Profile": "Roman Tile"},
                        sort_order=1,
                    ),
                ]
            ),
        )
        assert updated.price_from == Decimal("570.00")
        assert updated.price_to == Decimal("650.00")

        order_service = OrderService(session)
        selected_variation = updated.variations[1]
        order = await order_service.create_order(
            customer.id,
            OrderCreate(items=[OrderItemCreate(product_id=updated.id, variation_id=selected_variation.id, quantity=2)]),
        )
        assert order.total_amount == Decimal("1300.00")
        assert order.items[0].variation_id == selected_variation.id
        assert order.items[0].unit_price == Decimal("650.00")
        assert order.items[0].variation_snapshot["gauge"] == "28 Gauge"
        assert order.items[0].variation_snapshot["unit"] == "MTRS"
        assert updated.stock_quantity == 18

        try:
            await order_service.create_order(
                customer.id,
                OrderCreate(items=[OrderItemCreate(product_id=updated.id, quantity=1)]),
            )
        except HTTPException as error:
            assert error.status_code == 422
            assert "Select a variation" in error.detail
        else:
            raise AssertionError("Multi-option product was incorrectly orderable without a variation")

        legacy_product = await product_service.create(
            ProductCreate(
                name="Legacy Flashing",
                category_id=category.id,
                price_from=Decimal("400.00"),
                stock_quantity=5,
                unit="piece",
            )
        )
        legacy_order = await order_service.create_order(
            customer.id,
            OrderCreate(items=[OrderItemCreate(product_id=legacy_product.id, quantity=1)]),
        )
        assert legacy_order.items[0].variation_id is None
        assert legacy_order.items[0].unit_price == Decimal("400.00")
        assert legacy_order.items[0].variation_snapshot is None

    await engine.dispose()
    print("Service flow verified: variation pricing, independent update, selected order snapshot, and legacy fallback.")


if __name__ == "__main__":
    asyncio.run(run())
