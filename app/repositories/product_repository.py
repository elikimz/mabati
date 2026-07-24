"""Repository for Product database operations with search and filtering."""
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Product, ProductImage


class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _base_query(self):
        return (
            select(Product)
            .options(
                selectinload(Product.category),
                selectinload(Product.images),
            )
        )

    async def get_by_id(self, product_id: int) -> Optional[Product]:
        result = await self.db.execute(
            self._base_query().where(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Product]:
        result = await self.db.execute(
            self._base_query().where(Product.slug == slug)
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
        is_featured: Optional[bool] = None,
        product_type: Optional[str] = None,
        active_only: bool = True,
    ) -> Tuple[List[Product], int]:
        query = self._base_query()

        if active_only:
            query = query.where(Product.is_active == True)

        if search:
            query = query.where(
                or_(
                    Product.name.ilike(f"%{search}%"),
                    Product.description.ilike(f"%{search}%"),
                    Product.brand.ilike(f"%{search}%"),
                    Product.product_type.ilike(f"%{search}%"),
                    Product.material.ilike(f"%{search}%"),
                )
            )

        if category_id is not None:
            query = query.where(Product.category_id == category_id)

        if color:
            query = query.where(Product.color.ilike(f"%{color}%"))

        if gauge:
            query = query.where(Product.gauge == gauge)

        if min_price is not None:
            query = query.where(Product.price_from >= min_price)

        if max_price is not None:
            query = query.where(Product.price_from <= max_price)

        if in_stock is True:
            query = query.where(Product.stock_quantity > 0)
        elif in_stock is False:
            query = query.where(Product.stock_quantity == 0)

        if is_featured is not None:
            query = query.where(Product.is_featured == is_featured)

        if product_type:
            query = query.where(Product.product_type.ilike(f"%{product_type}%"))

        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        result = await self.db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all()), total

    async def get_featured(self, limit: int = 8) -> List[Product]:
        result = await self.db.execute(
            self._base_query()
            .where(Product.is_featured == True, Product.is_active == True)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_related(self, product: Product, limit: int = 6) -> List[Product]:
        result = await self.db.execute(
            self._base_query()
            .where(
                Product.category_id == product.category_id,
                Product.id != product.id,
                Product.is_active == True,
            )
            .limit(limit)
        )
        return list(result.scalars().all())

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

    async def add_image(self, image: ProductImage) -> ProductImage:
        self.db.add(image)
        await self.db.commit()
        await self.db.refresh(image)
        return image

    async def delete_image(self, image: ProductImage) -> None:
        await self.db.delete(image)
        await self.db.commit()

    async def get_image_by_id(self, image_id: int) -> Optional[ProductImage]:
        result = await self.db.execute(
            select(ProductImage).where(ProductImage.id == image_id)
        )
        return result.scalar_one_or_none()
