import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ContentStatus(str, enum.Enum):
    draft = "draft"
    pending_review = "pending_review"
    published = "published"
    archived = "archived"


class Content(Base, TimestampMixin):
    __tablename__ = "content"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False, default="")
    feature_image_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus, name="contentstatus"), nullable=False, default=ContentStatus.draft
    )
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    # Explicit DateTime(timezone=True): without it SQLAlchemy infers a bare
    # DateTime() from the `datetime` annotation, which Postgres creates as
    # TIMESTAMP WITHOUT TIME ZONE — then a tz-aware Python datetime.now(UTC)
    # write blows up with "can't subtract offset-naive and offset-aware
    # datetimes". Only ever surfaced against a real Postgres; the SQLite
    # in-memory test DB doesn't distinguish tz-aware/naive so this was
    # latent until the first real publish against Postgres.
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Rowling Room fields. topic_id IS NOT NULL is the discriminator for
    # "this post came out of a Topic reader"; style is a plain string (not
    # a Postgres enum) so a 4th writing style never needs an ALTER TYPE —
    # same precedent as PuzzleGameProgress.game_id. Validity is enforced by
    # a Literal[...] on the Pydantic schema instead.
    topic_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("topics.id"), nullable=True)
    style: Mapped[str | None] = mapped_column(String(50), nullable=True)
