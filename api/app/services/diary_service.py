import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus
from app.models.user import User
from app.services import content_service

DIARY_STYLE = "diary_entry"
DEFAULT_DIARY_THEME = "classic"


def _format_title(entry_date: date) -> str:
    # Human date used as the entry's title/identity, e.g. "Monday, 17 August 2026".
    return entry_date.strftime("%A, %-d %B %Y")


async def get_or_create_today(
    db: AsyncSession, user: User, entry_date: date, default_theme: str = DEFAULT_DIARY_THEME
) -> Content:
    """One diary entry per calendar day per learner. entry_date is the kid's
    local date, supplied by the client — so "today" matches their wall clock,
    not the server's UTC day."""
    result = await db.execute(
        select(Content).where(
            Content.author_id == user.id,
            Content.style == DIARY_STYLE,
            Content.entry_date == entry_date,
            Content.deleted_at.is_(None),
        )
    )
    entry = result.scalar_one_or_none()
    if entry is not None:
        return entry

    slug = await content_service._unique_slug(db, f"diary-{entry_date.isoformat()}")
    entry = Content(
        id=uuid.uuid4(),
        title=_format_title(entry_date),
        slug=slug,
        content_markdown="",
        status=ContentStatus.draft,
        author_id=user.id,
        topic_id=None,
        style=DIARY_STYLE,
        diary_theme=default_theme,
        entry_date=entry_date,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def list_entries(db: AsyncSession, user: User) -> list[Content]:
    result = await db.execute(
        select(Content)
        .where(
            Content.author_id == user.id,
            Content.style == DIARY_STYLE,
            Content.deleted_at.is_(None),
        )
        .order_by(Content.entry_date.desc())
    )
    return list(result.scalars().all())
