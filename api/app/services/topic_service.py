import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from slugify import slugify
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.topic import Topic, TopicStatus
from app.models.user import User
from app.schemas.topic import TopicCreate, TopicUpdate

_TOPIC_TRANSITIONS: dict[str, tuple[TopicStatus, TopicStatus]] = {
    "publish": (TopicStatus.draft, TopicStatus.published),
    "unpublish": (TopicStatus.published, TopicStatus.draft),
}


async def _unique_slug(db: AsyncSession, title: str) -> str:
    base = slugify(title) or "topic"
    slug = base
    suffix = 2
    while True:
        result = await db.execute(select(Topic.id).where(Topic.slug == slug))
        if result.scalar_one_or_none() is None:
            return slug
        slug = f"{base}-{suffix}"
        suffix += 1


async def create(db: AsyncSession, author: User, data: TopicCreate) -> Topic:
    slug = await _unique_slug(db, data.title)
    topic = Topic(
        id=uuid.uuid4(),
        title=data.title,
        slug=slug,
        explainer_markdown=data.explainer_markdown,
        audio_url=data.audio_url,
        order_index=data.order_index,
        status=TopicStatus.draft,
        author_id=author.id,
    )
    db.add(topic)
    await db.commit()
    await db.refresh(topic)
    return topic


async def update(db: AsyncSession, topic: Topic, data: TopicUpdate) -> Topic:
    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(topic, field, value)
    await db.commit()
    await db.refresh(topic)
    return topic


async def transition(db: AsyncSession, topic: Topic, action: str) -> Topic:
    from_status, to_status = _TOPIC_TRANSITIONS[action]
    if topic.status != from_status:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot {action} from status '{topic.status.value}'.",
        )
    # Audio is the actual lesson now (explainer_markdown is just a short
    # curiosity hook) — a topic with no audio has nothing to teach.
    if action == "publish" and not topic.audio_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Add narrated audio before publishing — audio is the lesson now.",
        )
    topic.status = to_status
    if action == "publish" and topic.published_at is None:
        topic.published_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(topic)
    return topic


async def delete(db: AsyncSession, topic: Topic) -> None:
    topic.deleted_at = datetime.now(UTC)
    await db.commit()


async def get_by_id(db: AsyncSession, topic_id: uuid.UUID) -> Topic | None:
    result = await db.execute(select(Topic).where(Topic.id == topic_id, Topic.deleted_at.is_(None)))
    return result.scalar_one_or_none()


async def get_published_by_slug(db: AsyncSession, slug: str) -> Topic | None:
    result = await db.execute(
        select(Topic).where(
            Topic.slug == slug,
            Topic.status == TopicStatus.published,
            Topic.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def list_published(db: AsyncSession) -> list[Topic]:
    result = await db.execute(
        select(Topic)
        .where(Topic.status == TopicStatus.published, Topic.deleted_at.is_(None))
        .order_by(Topic.order_index, Topic.created_at)
    )
    return list(result.scalars().all())


async def list_all(db: AsyncSession) -> list[Topic]:
    result = await db.execute(
        select(Topic).where(Topic.deleted_at.is_(None)).order_by(Topic.order_index, Topic.created_at)
    )
    return list(result.scalars().all())


def assert_owner(topic: Topic, current_user: User) -> None:
    if topic.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the author of this topic.")
