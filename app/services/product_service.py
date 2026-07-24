"""Product business logic service."""
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ProductRepository(db)
        self.cat_repo = CategoryRepository(db)

    async def _validate_category(self, category_id: int):
        cat = await self.cat_repo.get_by_id(category_id)
        if not cat:
            raise HTTPException(status_code=404, detail=f"Category {category_id} not found")
        return cat

    async def create(self, data: ProductCreate) -> Product:
        await self._validate_category(data.category_id)
        product = Product(**data.model_dump())
        return await self.repo.create(product)

    async def update(self, product_id: int, data: ProductUpdate) -> Product:
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        if data.category_id is not None:
            await self._validate_category(data.category_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(product, field, value)
        return await self.repo.update(product)

    async def delete(self, product_id: int) -> None:
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        await self.repo.delete(product)
