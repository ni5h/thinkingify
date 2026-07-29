import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class CompanionMessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"


class CompanionMessage(Base, TimestampMixin):
    """One turn in the writing companion's chat thread for a single draft.

    Scoped per (content_id, user_id), not per topic — a kid may write the
    same topic in multiple styles/attempts, each its own Content row and
    its own conversation. `session_id` is a plain, un-FK'd UUID generated
    client-side once per Writing Studio visit: it groups messages into the
    unit a future cross-session "stuck pattern" memory phase will
    summarize, without needing any table here to change shape when that
    phase adds its own aggregation tables.

    ladder_level/direct_answer_requested/fact_leak_blocked are populated
    on assistant rows only (null/False on user rows) and are re-derived by
    scanning this session's messages on each request rather than tracked
    as running counters — correct-by-construction at this feature's scale.
    """

    __tablename__ = "companion_messages"
    __table_args__ = (
        Index("ix_companion_messages_content_user_created", "content_id", "user_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("content.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    role: Mapped[CompanionMessageRole] = mapped_column(
        Enum(CompanionMessageRole, name="companionmessagerole"), nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    ladder_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    direct_answer_requested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fact_leak_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_fallback: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
