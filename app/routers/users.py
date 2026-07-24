"""User management router (admin only)."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_admin, get_current_user, get_db
from app.core.security import hash_password, verify_password
from app.repositories.user_repository import UserRepository
from app.schemas.user import PasswordChange, UserOut, UserUpdate

router = APIRouter(prefix="/admin/users", tags=["Users (Admin)"])


@router.get("/", response_model=List[UserOut])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    """List all users (admin only)."""
    repo = UserRepository(db)
    return await repo.get_all(skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    """Get a user by ID (admin only)."""
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    """Update a user's details (admin only)."""
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    return await repo.update(user)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """Delete a user (admin only)."""
    if user_id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await repo.delete(user)


# Self-service password change
profile_router = APIRouter(prefix="/users", tags=["Users"])


@profile_router.post("/change-password", status_code=200)
async def change_password(
    data: PasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Change the authenticated user's password."""
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    repo = UserRepository(db)
    current_user.hashed_password = hash_password(data.new_password)
    await repo.update(current_user)
    return {"message": "Password changed successfully"}
