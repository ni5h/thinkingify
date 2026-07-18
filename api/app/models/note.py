import uuid

from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Note(Base, TimestampMixin):
    """One evolving scratchpad per topic per learner — not a list of notes.

    Matches the spec's "persistent side panel, empty and ready to use"
    framing: a single mutable document, autosaved on blur (same pattern as
    the retired Journal module), not multiple named notes.
    """

    __tablename__ = "notes"
    __table_args__ = (UniqueConstraint("topic_id", "user_id", name="uq_notes_topic_user"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("topics.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
