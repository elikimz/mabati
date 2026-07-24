"""Authentication service: register, login, token refresh."""
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import Token, TokenRefresh
from app.schemas.user import UserCreate


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UserRepository(db)

    async def register(self, data: UserCreate) -> User:
        existing = await self.repo.get_by_email(data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        user = User(
            name=data.name,
            email=data.email,
            hashed_password=hash_password(data.password),
            role=data.role,
        )
        return await self.repo.create(user)

    async def login(self, email: str, password: str) -> Token:
        user = await self.repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive",
            )
        return Token(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )

    async def refresh(self, data: TokenRefresh) -> Token:
        from jose import JWTError

        try:
            payload = decode_token(data.refresh_token)
            if payload.get("type") != "refresh":
                raise ValueError("Not a refresh token")
            user_id = int(payload["sub"])
        except (JWTError, ValueError, KeyError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )
        user = await self.repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )
        return Token(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )
