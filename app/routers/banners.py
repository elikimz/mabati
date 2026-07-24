"""Router for landing page banner management."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.banner import Banner
from app.schemas.banner import BannerCreate, BannerUpdate, BannerOut
from app.routers.auth import get_current_user
from app.models.user import User

router = APIRouter(tags=["Banners"])

@router.get("/banners", response_model=List[BannerOut])
async def list_banners(
    location: Optional[str] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    query = select(Banner)
    if active_only:
        query = query.where(Banner.is_active == True)
    if location:
        query = query.where(Banner.location == location)
    
    query = query.order_by(Banner.display_order.asc(), Banner.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/admin/banners", response_model=BannerOut, status_code=status.HTTP_201_CREATED)
async def create_banner(
    data: BannerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "staff"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    banner = Banner(**data.model_dump())
    db.add(banner)
    await db.commit()
    await db.refresh(banner)
    return banner

@router.patch("/admin/banners/{banner_id}", response_model=BannerOut)
async def update_banner(
    banner_id: int,
    data: BannerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "staff"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    result = await db.execute(select(Banner).where(Banner.id == banner_id))
    banner = result.scalar_one_or_none()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(banner, key, value)
    
    await db.commit()
    await db.refresh(banner)
    return banner

@router.delete("/admin/banners/{banner_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_banner(
    banner_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "staff"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    result = await db.execute(select(Banner).where(Banner.id == banner_id))
    banner = result.scalar_one_or_none()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    
    await db.delete(banner)
    await db.commit()
    return None
