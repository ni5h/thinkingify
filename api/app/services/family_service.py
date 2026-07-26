import uuid
from datetime import UTC, datetime
from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.family_link import FamilyLink, FamilyLinkStatus
from app.models.user import User


async def _get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def send_request(
    db: AsyncSession, sender: User, target_email: str, target_role: Literal["guardian", "child"]
) -> FamilyLink:
    target = await _get_user_by_email(db, target_email)
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found for that email. Ask them to sign in with Google first, then send the request again.",
        )
    if target.id == sender.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You can't link to yourself.")

    # Orientation is decided by which of the two actions the sender picked
    # — no separate role column on the row itself.
    if target_role == "guardian":
        guardian_id, child_id = target.id, sender.id
    else:
        guardian_id, child_id = sender.id, target.id

    existing = await db.execute(
        select(FamilyLink.id).where(FamilyLink.guardian_id == guardian_id, FamilyLink.child_id == child_id)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="A request or link already exists between you two."
        )

    link = FamilyLink(
        id=uuid.uuid4(),
        guardian_id=guardian_id,
        child_id=child_id,
        requested_by=sender.id,
        status=FamilyLinkStatus.pending,
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return link


async def _get_link_or_404(db: AsyncSession, link_id: uuid.UUID) -> FamilyLink:
    result = await db.execute(select(FamilyLink).where(FamilyLink.id == link_id))
    link = result.scalar_one_or_none()
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.")
    return link


def _assert_party(link: FamilyLink, user: User) -> None:
    if user.id not in (link.guardian_id, link.child_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not part of this request.")


async def list_incoming(db: AsyncSession, user: User) -> list[FamilyLink]:
    result = await db.execute(
        select(FamilyLink).where(
            FamilyLink.status == FamilyLinkStatus.pending,
            FamilyLink.requested_by != user.id,
            or_(FamilyLink.guardian_id == user.id, FamilyLink.child_id == user.id),
        )
    )
    return list(result.scalars().all())


async def list_outgoing(db: AsyncSession, user: User) -> list[FamilyLink]:
    result = await db.execute(
        select(FamilyLink).where(
            FamilyLink.status == FamilyLinkStatus.pending,
            FamilyLink.requested_by == user.id,
        )
    )
    return list(result.scalars().all())


async def accept(db: AsyncSession, link_id: uuid.UUID, user: User) -> FamilyLink:
    link = await _get_link_or_404(db, link_id)
    _assert_party(link, user)
    if link.status != FamilyLinkStatus.pending:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This request is no longer pending.")
    if link.requested_by == user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can't accept your own request.")
    link.status = FamilyLinkStatus.accepted
    link.accepted_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(link)
    return link


async def decline(db: AsyncSession, link_id: uuid.UUID, user: User) -> None:
    link = await _get_link_or_404(db, link_id)
    _assert_party(link, user)
    if link.status != FamilyLinkStatus.pending:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This request is no longer pending.")
    if link.requested_by == user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can't decline your own request.")
    await db.delete(link)
    await db.commit()


async def list_my_links(db: AsyncSession, user: User) -> tuple[list[FamilyLink], list[FamilyLink]]:
    as_guardian = await db.execute(
        select(FamilyLink).where(FamilyLink.guardian_id == user.id, FamilyLink.status == FamilyLinkStatus.accepted)
    )
    as_child = await db.execute(
        select(FamilyLink).where(FamilyLink.child_id == user.id, FamilyLink.status == FamilyLinkStatus.accepted)
    )
    return list(as_guardian.scalars().all()), list(as_child.scalars().all())


async def unlink(db: AsyncSession, link_id: uuid.UUID, user: User) -> None:
    link = await _get_link_or_404(db, link_id)
    _assert_party(link, user)
    if link.status != FamilyLinkStatus.accepted:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This link isn't active.")
    await db.delete(link)
    await db.commit()


async def is_accepted_guardian(db: AsyncSession, guardian_id: uuid.UUID, child_id: uuid.UUID) -> bool:
    result = await db.execute(
        select(FamilyLink.id).where(
            FamilyLink.guardian_id == guardian_id,
            FamilyLink.child_id == child_id,
            FamilyLink.status == FamilyLinkStatus.accepted,
        )
    )
    return result.scalar_one_or_none() is not None


async def has_any_accepted_guardian(db: AsyncSession, child_id: uuid.UUID) -> bool:
    result = await db.execute(
        select(FamilyLink.id).where(FamilyLink.child_id == child_id, FamilyLink.status == FamilyLinkStatus.accepted)
    )
    return result.scalar_one_or_none() is not None


async def assert_accepted_guardian_of(db: AsyncSession, guardian: User, child_id: uuid.UUID) -> User:
    result = await db.execute(select(User).where(User.id == child_id))
    child = result.scalar_one_or_none()
    if child is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such user.")
    if not await is_accepted_guardian(db, guardian_id=guardian.id, child_id=child_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not an accepted guardian of this user.")
    return child


async def assert_linked(db: AsyncSession, viewer: User, other_user_id: uuid.UUID) -> User:
    """Permission check for viewing another user's profile: allowed if
    it's your own id, or either party is an accepted guardian of the
    other. Bidirectional, so it serves both "child views guardian" and
    "guardian views child" with one function."""
    result = await db.execute(select(User).where(User.id == other_user_id))
    other = result.scalar_one_or_none()
    if other is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such user.")
    if viewer.id == other_user_id:
        return other
    if await is_accepted_guardian(db, guardian_id=viewer.id, child_id=other_user_id):
        return other
    if await is_accepted_guardian(db, guardian_id=other_user_id, child_id=viewer.id):
        return other
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not linked to this user.")


async def users_by_id(db: AsyncSession, user_ids: set[uuid.UUID]) -> dict[uuid.UUID, User]:
    """Batch lookup so serializing a list of links doesn't N+1 — no
    SQLAlchemy relationships on FamilyLink, matching this codebase's
    existing convention of plain FK columns everywhere (Content/Topic have
    no .author relationship either)."""
    if not user_ids:
        return {}
    result = await db.execute(select(User).where(User.id.in_(user_ids)))
    return {u.id: u for u in result.scalars().all()}
