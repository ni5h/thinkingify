import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class SpellingErrorType(str, enum.Enum):
    misspelling = "misspelling"
    homophone = "homophone"


class SpellingFlagStatus(str, enum.Enum):
    pending = "pending"
    self_corrected = "self_corrected"
    kept_as_is = "kept_as_is"


class SpellingFlag(Base, TimestampMixin):
    """One flagged word for one draft, keyed by (content_id, word).

    A row is upserted, not recreated, on every re-check — `word` is the
    lowercased token identity, so the same misspelling appearing in
    multiple sentences (or multiple Rowling sections) is still exactly one
    row, matching the app's document-wide dedup decision. `status` models
    the terminal outcome only (still open / fixed / explicitly kept);
    `hint_revealed` is a separate flag because a revealed hint doesn't
    change that outcome — the kid still has to explicitly apply the shown
    answer, so the flag stays `pending` until they do.
    """

    __tablename__ = "spelling_flags"
    __table_args__ = (
        UniqueConstraint("content_id", "word", name="uq_spelling_flags_content_word"),
        Index("ix_spelling_flags_content_status", "content_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("content.id"), nullable=False)
    word: Mapped[str] = mapped_column(String(100), nullable=False)
    error_type: Mapped[SpellingErrorType] = mapped_column(
        Enum(SpellingErrorType, name="spellingerrortype"), nullable=False
    )
    context_sentence: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_correction: Mapped[str | None] = mapped_column(Text, nullable=True)
    hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[SpellingFlagStatus] = mapped_column(
        Enum(SpellingFlagStatus, name="spellingflagstatus"), nullable=False, default=SpellingFlagStatus.pending
    )
    hint_revealed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
