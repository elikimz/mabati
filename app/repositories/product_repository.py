"""Repository for Product database operations with search and filtering."""
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Product


class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, product_id: int) -> Optional[Product]:
        result = await self.db.execute(
            select(Product)
            .options(selectinload(Product.category))
            .where(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        category_id: Optional[int] = None,
        color: Optional[str] = None,
        gauge: Optional[str] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        in_stock: Optional[bool] = None,
        active_only: bool = True,
    ) -> Tuple[List[Product], int]:
        query = select(Product).options(selectinload(Product.category))

        if active_only:
            query = query.where(Product.is_active == True)
        if search:
            query = query.where(
                or_(
                    Product.name.ilike(f"%{search}%"),
                    Product.description.ilike(f"%{search}%"),
                    Product.brand.ilike(f"%{search}%"),
                )
            )
        if category_id is not None:
            query = query.where(Product.category_id == category_id)
        if color:
            query = query.where(Product.color.ilike(f"%{color}%"))
        if gauge:
            query = query.where(Product.gauge == gauge)
        if min_price is not None:
            query = query.where(Product.price >= min_price)
        if max_price is not None:
            query = query.where(Product.price <= max_price)
        if in_stock is True:
            query = query.where(Product.stock_quantity > 0)
        elif in_stock is False:
            query = query.where(Product.stock_quantity == 0)

        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        result = await self.db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all()), total

    async def get_low_stock(self) -> List[Product]:
        result = await self.db.execute(
            select(Product).where(
                Product.stock_quantity <= Product.low_stock_threshold,
                Product.is_active == True,
            )
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(Product))
        return result.scalar_one()

    async def create(self, product: Product) -> Product:
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return await self.get_by_id(product.id)

    async def update(self, product: Product) -> Product:
        await self.db.commit()
        await self.db.refresh(product)
        return await self.get_by_id(product.id)

    async def delete(self, product: Product) -> None:
        await self.db.delete(product)
        await self.db.commit()
