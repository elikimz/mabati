"""Authentication router: register, login, refresh, me."""
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.schemas.auth import Token, TokenRefresh
from app.schemas.user import UserCreate, UserOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=201)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    service = AuthService(db)
    return await service.register(data)


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Login with email and password, returns JWT tokens."""
    service = AuthService(db)
    return await service.login(form_data.username, form_data.password)


@router.post("/refresh", response_model=Token)
async def refresh_token(data: TokenRefresh, db: AsyncSession = Depends(get_db)):
    """Obtain a new access token using a valid refresh token."""
    service = AuthService(db)
    return await service.refresh(data)


@router.get("/me", response_model=UserOut)
async def get_me(current_user=Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return current_user
