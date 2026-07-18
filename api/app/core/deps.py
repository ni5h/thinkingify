import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User, UserRole

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials)
        sub: str = payload.get("sub")
        if sub is None:
            raise credentials_exception
        if payload.get("type") == "refresh":
            raise credentials_exception
        user_id = uuid.UUID(sub)
    except (JWTError, ValueError):
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


def _role_guard(*roles: UserRole):
    async def guard(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return guard


require_admin = _role_guard(UserRole.admin)
require_author_or_admin = _role_guard(UserRole.author, UserRole.admin)
require_learner_or_admin = _role_guard(UserRole.learner, UserRole.admin)
# Any role that can own Content (author's Blog posts, learner's Rowling
# Room posts). Ownership is still enforced per-call via
# assert_owner_or_admin/_get_owned_or_404 — this only widens *who can act
# on content at all*, not which rows they can touch.
require_content_actor = _role_guard(UserRole.author, UserRole.learner, UserRole.admin)
