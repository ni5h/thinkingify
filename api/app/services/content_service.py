import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from slugify import slugify
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus
from app.models.user import User, UserRole
from app.schemas.content import ContentCreate, ContentUpdate

# Legal status transitions, matching the button-gated state machine of the
# original localStorage BlogService. Enforced server-side now (409 on an
# illegal transition) instead of trusted purely via which buttons the UI shows.
_TRANSITIONS: dict[str, tuple[ContentStatus, ContentStatus]] = {
    "submit_for_review": (ContentStatus.draft, ContentStatus.pending_review),
    "back_to_draft": (ContentStatus.pending_review, ContentStatus.draft),
    "publish": (ContentStatus.pending_review, ContentStatus.published),
    "archive": (ContentStatus.published, ContentStatus.archived),
    "republish": (ContentStatus.archived, ContentStatus.published),
    # Learner self-publish path: draft straight to published, no admin
    # review step. Kept as distinct transitions (rather than reusing
    # "publish"/"republish") so the admin-only publish endpoints stay
    # untouched — see require_content_actor vs. require_admin in deps.py.
    "self_publish": (ContentStatus.draft, ContentStatus.published),
    "self_republish": (ContentStatus.archived, ContentStatus.published),
}
_DELETABLE_STATUSES = {ContentStatus.draft, ContentStatus.archived}


async def _unique_slug(db: AsyncSession, title: str) -> str:
    base = slugify(title) or "post"
    slug = base
    suffix = 2
    while True:
        result = await db.execute(select(Content.id).where(Content.slug == slug))
        if result.scalar_one_or_none() is None:
            return slug
        slug = f"{base}-{suffix}"
        suffix += 1


async def create(db: AsyncSession, author: User, data: ContentCreate) -> Content:
    slug = await _unique_slug(db, data.title)
    content = Content(
        id=uuid.uuid4(),
        title=data.title,
        slug=slug,
        summary=data.summary,
        content_markdown=data.content_markdown,
        status=ContentStatus.draft,
        author_id=author.id,
        topic_id=data.topic_id,
        style=data.style,
    )
    db.add(content)
    await db.commit()
    await db.refresh(content)
    return content


async def update(db: AsyncSession, content: Content, data: ContentUpdate) -> Content:
    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(content, field, value)
    await db.commit()
    await db.refresh(content)
    return content


async def transition(db: AsyncSession, content: Content, action: str) -> Content:
    from_status, to_status = _TRANSITIONS[action]
    if content.status != from_status:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot {action.replace('_', ' ')} from status '{content.status.value}'.",
        )
    content.status = to_status
    if action in ("publish", "self_publish") and content.published_at is None:
        content.published_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(content)
    return content


async def delete(db: AsyncSession, content: Content) -> None:
    if content.status not in _DELETABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete from status '{content.status.value}'.",
        )
    content.deleted_at = datetime.now(UTC)
    await db.commit()


async def get_by_id(db: AsyncSession, content_id: uuid.UUID) -> Content | None:
    result = await db.execute(
        select(Content).where(Content.id == content_id, Content.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def get_published_by_slug(db: AsyncSession, slug: str) -> Content | None:
    result = await db.execute(
        select(Content).where(
            Content.slug == slug,
            Content.status == ContentStatus.published,
            Content.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def list_published(db: AsyncSession) -> list[Content]:
    result = await db.execute(
        select(Content)
        .where(Content.status == ContentStatus.published, Content.deleted_at.is_(None))
        .order_by(Content.published_at.desc())
    )
    return list(result.scalars().all())


async def list_all(db: AsyncSession, current_user: User) -> list[Content]:
    query = select(Content).where(Content.deleted_at.is_(None))
    if current_user.role != UserRole.admin:
        query = query.where(Content.author_id == current_user.id)
    query = query.order_by(Content.updated_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


def assert_owner_or_admin(content: Content, current_user: User) -> None:
    if current_user.role == UserRole.admin:
        return
    if content.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the author of this post.")
