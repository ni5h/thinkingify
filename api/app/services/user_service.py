import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import ProfileUpdate, UserPublicSummary


async def _assert_username_available(db: AsyncSession, username: str, excluding_user_id: uuid.UUID) -> None:
    result = await db.execute(
        select(User.id).where(User.username == username, User.id != excluding_user_id)
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="That username is already taken.")


async def update_profile(db: AsyncSession, user: User, data: ProfileUpdate) -> User:
    changes = data.model_dump(exclude_unset=True)

    if "username" in changes and changes["username"] is not None:
        await _assert_username_available(db, changes["username"], user.id)

    for field, value in changes.items():
        setattr(user, field, value)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="That username is already taken."
        ) from exc

    await db.refresh(user)
    return user


async def public_summaries_by_id(db: AsyncSession, user_ids: set[uuid.UUID]) -> dict[uuid.UUID, UserPublicSummary]:
    """Batch lookup returning the privacy-filtered public tier, so callers
    (e.g. blog byline serialization) can never reach for .last_name or
    .location_* — matches family_service.users_by_id's no-relationship()
    batch-lookup convention, but returns the filtered schema, not raw rows."""
    if not user_ids:
        return {}
    result = await db.execute(select(User).where(User.id.in_(user_ids)))
    return {u.id: UserPublicSummary.from_user(u) for u in result.scalars().all()}
