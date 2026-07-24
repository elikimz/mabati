"""Category business logic service."""
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CategoryRepository(db)

    async def create(self, data: CategoryCreate) -> Category:
        existing = await self.repo.get_by_name(data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Category '{data.name}' already exists",
            )
        category = Category(**data.model_dump())
        return await self.repo.create(category)

    async def update(self, category_id: int, data: CategoryUpdate) -> Category:
        category = await self.repo.get_by_id(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        if data.name and data.name != category.name:
            existing = await self.repo.get_by_name(data.name)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Category '{data.name}' already exists",
                )
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(category, field, value)
        return await self.repo.update(category)

    async def delete(self, category_id: int) -> None:
        category = await self.repo.get_by_id(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        await self.repo.delete(category)
