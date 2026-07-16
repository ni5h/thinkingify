from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.auth import AccessTokenResponse, GoogleAuthRequest, RefreshRequest, TokenResponse
from app.schemas.user import UserOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/google", response_model=TokenResponse)
async def google_sign_in(body: GoogleAuthRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    return await auth_service.google_sign_in(body.id_token, db)


@router.post("/dev-login", response_model=TokenResponse)
async def dev_login(db: Annotated[AsyncSession, Depends(get_db)]):
    if not settings.allow_dev_login:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Dev login is not enabled.")
    return await auth_service.dev_login(db)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_token(body: RefreshRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    return await auth_service.refresh_access_token(body.refresh_token, db)


@router.get("/me", response_model=UserOut)
async def me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user
