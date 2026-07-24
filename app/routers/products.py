"""Products router — public browsing + admin CRUD + image management."""
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_admin, get_db
from app.repositories.product_repository import ProductRepository
from app.schemas.product import (
    ProductCreate,
    ProductImageCreate,
    ProductImageOut,
    ProductListOut,
    ProductOut,
    ProductUpdate,
)
from app.services.product_service import ProductService

router = APIRouter(tags=["Products"])


@router.get("/products", response_model=List[ProductListOut])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None),
    category: Optional[int] = Query(None, alias="category_id"),
    color: Optional[str] = Query(None),
    gauge: Optional[str] = Query(None),
    min_price: Optional[Decimal] = Query(None),
    max_price: Optional[Decimal] = Query(None),
    in_stock: Optional[bool] = Query(None),
    is_featured: Optional[bool] = Query(None),
    product_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    repo = ProductRepository(db)
    products, _ = await repo.get_all(
        skip=skip, limit=limit, search=search, category_id=category,
        color=color, gauge=gauge, min_price=min_price, max_price=max_price,
        in_stock=in_stock, is_featured=is_featured, product_type=product_type,
    )
    return products


@router.get("/products/featured", response_model=List[ProductListOut])
async def get_featured_products(
    limit: int = Query(8, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """Return featured products for homepage showcase."""
    repo = ProductRepository(db)
    return await repo.get_featured(limit=limit)


@router.get("/products/slug/{slug}", response_model=ProductOut)
async def get_product_by_slug(slug: str, db: AsyncSession = Depends(get_db)):
    repo = ProductRepository(db)
    product = await repo.get_by_slug(slug)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/products/{product_id}", response_model=ProductOut)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    repo = ProductRepository(db)
    product = await repo.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/products/{product_id}/related", response_model=List[ProductListOut])
async def get_related_products(
    product_id: int,
    limit: int = Query(6, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
):
    service = ProductService(db)
    return await service.get_related(product_id, limit=limit)


@router.post("/admin/products", response_model=ProductOut, status_code=201)
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    service = ProductService(db)
    return await service.create(data)


@router.put("/admin/products/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    service = ProductService(db)
    return await service.update(product_id, data)


@router.delete("/admin/products/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    service = ProductService(db)
    await service.delete(product_id)


@router.post("/admin/products/{product_id}/images", response_model=ProductImageOut, status_code=201)
async def add_product_image(
    product_id: int,
    data: ProductImageCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    service = ProductService(db)
    return await service.add_image(product_id, data)


@router.delete("/admin/products/{product_id}/images/{image_id}", status_code=204)
async def delete_product_image(
    product_id: int,
    image_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    service = ProductService(db)
    await service.delete_image(product_id, image_id)
