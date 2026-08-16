import uuid

from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Note(Base, TimestampMixin):
    """One evolving scratchpad per learner, keyed by exactly one of topic or
    content — not a list of notes.

    Matches the spec's "persistent side panel, empty and ready to use"
    framing: a single mutable document, autosaved on blur (same pattern as
    the retired Journal module), not multiple named notes. Topic-linked
    posts scope the note by topic (shared across every draft of that topic);
    a blank "Write your own" post has no topic, so its scratchpad is scoped
    by the content row itself.
    """

    __tablename__ = "notes"
    __table_args__ = (
        UniqueConstraint("topic_id", "user_id", name="uq_notes_topic_user"),
        UniqueConstraint("content_id", "user_id", name="uq_notes_content_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("topics.id"), nullable=True)
    content_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("content.id"), nullable=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
