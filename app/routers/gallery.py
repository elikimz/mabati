"""Gallery router — public listing + admin CRUD."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.cache import cache_response, invalidate_cache
from app.core.dependencies import get_db, get_current_admin
from app.models.gallery import Gallery
from app.schemas.gallery import GalleryCreate, GalleryUpdate, GalleryOut

router = APIRouter(prefix="/gallery", tags=["Gallery"])

@router.get("", response_model=List[GalleryOut])
@cache_response(prefix="gallery", ttl=900)  # 15 min cache
async def list_gallery(active_only: bool = True, db: AsyncSession = Depends(get_db)):
    query = select(Gallery)
    if active_only:
        query = query.where(Gallery.is_active == True)
    query = query.order_by(Gallery.display_order.asc(), Gallery.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

@router.post("", response_model=GalleryOut, status_code=status.HTTP_201_CREATED)
async def create_gallery(
    data: GalleryCreate, 
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    gallery = Gallery(**data.model_dump())
    db.add(gallery)
    await db.commit()
    await db.refresh(gallery)
    await invalidate_cache(prefix="gallery")
    return gallery

@router.patch("/{id}", response_model=GalleryOut)
async def update_gallery(
    id: int, 
    data: GalleryUpdate, 
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    result = await db.execute(select(Gallery).where(Gallery.id == id))
    gallery = result.scalar_one_or_none()
    if not gallery:
        raise HTTPException(status_code=404, detail="Gallery item not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(gallery, key, value)
        
    await db.commit()
    await db.refresh(gallery)
    await invalidate_cache(prefix="gallery")
    return gallery
