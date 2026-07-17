import uuid

from fastapi import HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.models.user import User, UserRole
from app.schemas.auth import AccessTokenResponse, TokenResponse
from app.schemas.user import UserOut


def _resolve_role(email: str) -> UserRole:
    """Reject sign-in outright for any email not on an allow-list.

    Unlike an open-signup + manual-promotion flow, no User row is created for
    an unrecognized email — accounts only ever land in Admin/Author/Learner,
    never an anonymous default role.
    """
    normalized = email.lower()
    if normalized in settings.admin_emails_set:
        return UserRole.admin
    if normalized in settings.author_emails_set:
        return UserRole.author
    if normalized in settings.learner_emails_set:
        return UserRole.learner
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="This email is not authorized for Thinkingify.",
    )


def _issue_tokens(user: User) -> TokenResponse:
    access_token = create_access_token(
        str(user.id), email=user.email, name=user.name, role=user.role.value
    )
    refresh_token = create_refresh_token(str(user.id))
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserOut.model_validate(user),
    )


async def google_sign_in(token: str, db: AsyncSession) -> TokenResponse:
    info = google_id_token.verify_oauth2_token(
        token, google_requests.Request(), settings.google_client_id
    )
    google_sub: str = info["sub"]
    email: str = info["email"]
    name: str = info.get("name", email)
    avatar_url: str | None = info.get("picture")

    # Role is re-resolved on every login (not just at creation) so that
    # editing ADMIN_EMAILS/AUTHOR_EMAILS takes effect immediately without a
    # manual promotion step.
    role = _resolve_role(email)

    result = await db.execute(select(User).where(User.google_sub == google_sub))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            id=uuid.uuid4(),
            google_sub=google_sub,
            email=email,
            name=name,
            avatar_url=avatar_url,
            role=role,
        )
        db.add(user)
    else:
        user.name = name
        user.avatar_url = avatar_url
        user.role = role

    await db.commit()
    await db.refresh(user)

    return _issue_tokens(user)


DEV_USER_GOOGLE_SUB = "dev-nish"
DEV_USER_EMAIL = "nish@thinkingify.dev"
DEV_USER_NAME = "nish"


async def dev_login(db: AsyncSession) -> TokenResponse:
    """Fixed test identity that bypasses Google sign-in and the allow-list
    entirely. Callers must check settings.allow_dev_login before invoking
    this — it is not checked here."""
    result = await db.execute(select(User).where(User.google_sub == DEV_USER_GOOGLE_SUB))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            id=uuid.uuid4(),
            google_sub=DEV_USER_GOOGLE_SUB,
            email=DEV_USER_EMAIL,
            name=DEV_USER_NAME,
            role=UserRole.admin,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return _issue_tokens(user)


async def refresh_access_token(refresh_token: str, db: AsyncSession) -> AccessTokenResponse:
    invalid_exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise invalid_exc
        user_id = uuid.UUID(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        raise invalid_exc

    result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return AccessTokenResponse(
        access_token=create_access_token(str(user.id), email=user.email, name=user.name, role=user.role.value)
    )
