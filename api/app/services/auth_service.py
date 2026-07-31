import uuid

from fastapi import HTTPException, status
from fastapi.concurrency import run_in_threadpool
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.models.user import User, UserRole
from app.schemas.auth import AccessTokenResponse, TokenResponse
from app.schemas.user import UserOut


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


async def _get_or_create_user(
    db: AsyncSession, *, google_sub: str, email: str, name: str, avatar_url: str | None = None
) -> User:
    # Open sign-up: any Google account (or the dev identity) gets a User
    # row. `role` is a fixed default here — nothing reads it for
    # authorization anymore (see api/app/core/deps.py), it only exists
    # because the DB column is NOT NULL. Real access control is
    # ownership-based (see content_service.assert_owner /
    # topic_service.assert_owner), not role-based.
    result = await db.execute(select(User).where(User.google_sub == google_sub))
    user = result.scalar_one_or_none()
    if user is not None:
        # Existing user — deliberately not re-syncing name/avatar_url from
        # Google here. Google is just the initial seed; a user who's
        # customized first_name/avatar_url via the Profile page shouldn't
        # have it silently clobbered by their next login.
        return user

    user = User(
        id=uuid.uuid4(),
        google_sub=google_sub,
        email=email,
        name=name,
        avatar_url=avatar_url,
        role=UserRole.learner,
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        # Lost a race with a concurrent sign-in for the same account —
        # e.g. an impatient double-click on the Google button firing a
        # second request while the first was still in flight, or two
        # tabs signing in at once. The other request already created the
        # row (google_sub/email are unique columns); pick it up instead
        # of 500ing.
        await db.rollback()
        result = await db.execute(select(User).where(User.google_sub == google_sub))
        return result.scalar_one()

    await db.refresh(user)
    return user


async def google_sign_in(token: str, db: AsyncSession) -> TokenResponse:
    # verify_oauth2_token makes a blocking network call (fetching/
    # validating Google's certs) — run it off the event loop so it
    # doesn't stall every other in-flight request on this worker.
    info = await run_in_threadpool(
        google_id_token.verify_oauth2_token, token, google_requests.Request(), settings.google_client_id
    )
    user = await _get_or_create_user(
        db,
        google_sub=info["sub"],
        email=info["email"],
        name=info.get("name", info["email"]),
        avatar_url=info.get("picture"),
    )
    return _issue_tokens(user)


DEV_USER_GOOGLE_SUB = "dev-nish"
DEV_USER_EMAIL = "nish@thinkingify.dev"
DEV_USER_NAME = "nish"


async def dev_login(db: AsyncSession) -> TokenResponse:
    """Fixed test identity that bypasses Google sign-in entirely. Callers
    must check settings.allow_dev_login before invoking this — it is not
    checked here."""
    user = await _get_or_create_user(db, google_sub=DEV_USER_GOOGLE_SUB, email=DEV_USER_EMAIL, name=DEV_USER_NAME)
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
