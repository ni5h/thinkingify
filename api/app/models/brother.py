import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class BrotherTierStatus(str, enum.Enum):
    locked = "locked"
    active = "active"
    mastered = "mastered"


class BrotherSessionStatus(str, enum.Enum):
    active = "active"
    complete = "complete"


class BrotherTierProgress(Base, TimestampMixin):
    """Per-user, per-tier mastery state. Only the durable facts live here —
    `median_ms`/`accuracy` are DERIVED from the attempt log at read time
    (avoids the "forgot to update the counter" class of staleness, same as
    Kakooma deriving its stats). `baseline_ms` is set once from the first
    10 attempts and never recomputed; `mastered_at` marks the boundary
    Phase B's retention window will read from.
    """

    __tablename__ = "brother_tier_progress"
    __table_args__ = (UniqueConstraint("user_id", "tier_id", name="uq_brother_tier_progress_user_tier"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    tier_id: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[BrotherTierStatus] = mapped_column(
        Enum(BrotherTierStatus, name="brothertierstatus"), nullable=False, default=BrotherTierStatus.locked
    )
    baseline_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mastered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BrotherAttempt(Base, TimestampMixin):
    """Append-only answer log — the substrate every mastery calc queries.
    `correct` is server-computed (never client-trusted). `is_retention`/
    `is_preview` default False and are unused in Phase A; they exist now so
    Phase B's 70/20/10 mix + demotion need no migration.
    """

    __tablename__ = "brother_attempts"
    __table_args__ = (Index("ix_brother_attempts_user_tier_created", "user_id", "tier_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    tier_id: Mapped[str] = mapped_column(String(10), nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    correct_answer: Mapped[int] = mapped_column(Integer, nullable=False)
    user_answer: Mapped[int] = mapped_column(Integer, nullable=False)
    correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    response_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    is_retention: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_preview: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class BrotherSession(Base, TimestampMixin):
    """One drill session. The server owns the issued question set (`questions`
    JSON, WITHOUT correct answers) so answers are checked against a real
    issued set — the integrity guarantee the mastery signal depends on.
    """

    __tablename__ = "brother_sessions"
    __table_args__ = (Index("ix_brother_sessions_user_created", "user_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    questions: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[BrotherSessionStatus] = mapped_column(
        Enum(BrotherSessionStatus, name="brothersessionstatus"), nullable=False, default=BrotherSessionStatus.active
    )
    answered_indexes: Mapped[list[int]] = mapped_column(JSON, nullable=False, default=list)
