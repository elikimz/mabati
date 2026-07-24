"""Category router: public listing and admin CRUD."""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_admin, get_db
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate
from app.services.category_service import CategoryService

router = APIRouter(tags=["Categories"])


# ── Public ──────────────────────────────────────────────────────────────────

@router.get("/categories", response_model=List[CategoryOut])
async def list_categories(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """List all active categories."""
    repo = CategoryRepository(db)
    return await repo.get_all(skip=skip, limit=limit, active_only=True)


# ── Admin ────────────────────────────────────────────────────────────────────

@router.post("/admin/categories", response_model=CategoryOut, status_code=201)
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    """Create a new product category (admin only)."""
    service = CategoryService(db)
    return await service.create(data)


@router.put("/admin/categories/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    """Update an existing category (admin only)."""
    service = CategoryService(db)
    return await service.update(category_id, data)


@router.delete("/admin/categories/{category_id}", status_code=204)
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    """Delete a category (admin only)."""
    service = CategoryService(db)
    await service.delete(category_id)
