import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class TopicStatus(str, enum.Enum):
    draft = "draft"
    published = "published"


class Topic(Base, TimestampMixin):
    __tablename__ = "topics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    # Chunked via markdown ## headers, same round-trip convention as Content.content_markdown.
    # Inline images/diagrams are embedded as ![](url) markdown, not a separate table.
    explainer_markdown: Mapped[str] = mapped_column(Text, nullable=False, default="")
    audio_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    # Plain string tags, not a Theme table/FK — same "no DB enum, never
    # needs an ALTER TYPE" philosophy as Content.style. See ui's
    # core/models/theme.ts for the curated catalog these are drawn from.
    # JSON (not postgresql.ARRAY) so the sqlite-backed test suite can
    # create this table too — all theme filtering happens client-side, so
    # there's no need for Postgres's native array query operators here.
    themes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list, server_default="[]")
    status: Mapped[TopicStatus] = mapped_column(
        Enum(TopicStatus, name="topicstatus"), nullable=False, default=TopicStatus.draft
    )
    # Admin-controlled display order on the room landing grid — no algorithmic/random selection in v1.
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    # Explicit DateTime(timezone=True) — see the matching comment on
    # Content.published_at for why this is required, not decorative.
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
