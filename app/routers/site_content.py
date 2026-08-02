"""Site content router — public settings + admin CRUD."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.cache import cache_response, invalidate_cache
from app.core.dependencies import get_db, get_current_admin
from app.models.site_content import SiteContent
from app.schemas.site_content import SiteContentCreate, SiteContentUpdate, SiteContentOut

router = APIRouter(prefix="/site-content", tags=["Site Content"])

@router.get("", response_model=List[SiteContentOut])
@cache_response(prefix="site_content", ttl=900)  # 15 min cache
async def list_site_content(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SiteContent))
    return result.scalars().all()

@router.get("/{key}", response_model=SiteContentOut)
@cache_response(prefix="site_content:key", ttl=900)  # 15 min cache
async def get_site_content(key: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SiteContent).where(SiteContent.key == key))
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    return content

@router.post("", response_model=SiteContentOut, status_code=status.HTTP_201_CREATED)
async def create_or_update_site_content(
    data: SiteContentCreate, 
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    result = await db.execute(select(SiteContent).where(SiteContent.key == data.key))
    content = result.scalar_one_or_none()
    
    if content:
        content.value = data.value
        content.description = data.description
    else:
        content = SiteContent(**data.model_dump())
        db.add(content)
        
    await db.commit()
    await db.refresh(content)
    await invalidate_cache(prefix="site_content")
    return content

@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_site_content(
    key: str, 
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    result = await db.execute(select(SiteContent).where(SiteContent.key == key))
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    await db.delete(content)
    await db.commit()
    await invalidate_cache(prefix="site_content")
    return None
