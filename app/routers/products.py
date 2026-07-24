"""Product router: public listing/search and admin CRUD."""
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_admin, get_db
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductListOut, ProductOut, ProductUpdate
from app.services.product_service import ProductService

router = APIRouter(tags=["Products"])


# ── Public ──────────────────────────────────────────────────────────────────

@router.get("/products", response_model=List[ProductListOut])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None, description="Search by name, description, or brand"),
    category: Optional[int] = Query(None, alias="category_id"),
    color: Optional[str] = None,
    gauge: Optional[str] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    in_stock: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    List products with optional search and filters.

    - **search**: full-text search across name, description, brand
    - **category_id**: filter by category
    - **color**: filter by colour
    - **gauge**: filter by gauge/thickness
    - **min_price / max_price**: price range filter
    - **in_stock**: true = only in-stock items
    """
    repo = ProductRepository(db)
    products, _ = await repo.get_all(
        skip=skip,
        limit=limit,
        search=search,
        category_id=category,
        color=color,
        gauge=gauge,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
    )
    return products


@router.get("/products/{product_id}", response_model=ProductOut)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single product by ID."""
    repo = ProductRepository(db)
    product = await repo.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


# ── Admin ────────────────────────────────────────────────────────────────────

@router.post("/admin/products", response_model=ProductOut, status_code=201)
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    """Create a new product (admin only)."""
    service = ProductService(db)
    return await service.create(data)


@router.put("/admin/products/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    """Update a product (admin only)."""
    service = ProductService(db)
    return await service.update(product_id, data)


@router.delete("/admin/products/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    """Delete a product (admin only)."""
    service = ProductService(db)
    await service.delete(product_id)
