"""Repository for Category database operations."""
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category


class CategoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, category_id: int) -> Optional[Category]:
        result = await self.db.execute(select(Category).where(Category.id == category_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Category]:
        result = await self.db.execute(select(Category).where(Category.name == name))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[Category]:
        query = select(Category)
        if active_only:
            query = query.where(Category.is_active == True)
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(Category))
        return result.scalar_one()

    async def create(self, category: Category) -> Category:
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def update(self, category: Category) -> Category:
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def delete(self, category: Category) -> None:
        await self.db.delete(category)
        await self.db.commit()
