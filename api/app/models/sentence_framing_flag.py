import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class SentenceFramingFlagStatus(str, enum.Enum):
    pending = "pending"
    self_corrected = "self_corrected"
    kept_as_is = "kept_as_is"


class SentenceFramingFlag(Base, TimestampMixin):
    """One flagged *run* of consecutive sentences for one draft, keyed by
    (content_id, concept_id, sentences) — unlike SpellingFlag (one word)
    or GrammarFlag (one sentence), the thing being flagged here is a
    sequence (e.g. three sentences in a row starting with "I"), so
    `sentences` holds the whole flagged run space-joined — both the
    dedup key and the pre-filled textarea content the kid rewrites.

    No hint/example columns, same reasoning as GrammarFlag — that
    content is a pure function of concept_id, resolved from
    sentence_framing_concepts.py at response-assembly time.
    """

    __tablename__ = "sentence_framing_flags"
    __table_args__ = (
        UniqueConstraint(
            "content_id", "concept_id", "sentences", name="uq_sentence_framing_flags_content_concept_sentences"
        ),
        Index("ix_sentence_framing_flags_content_status", "content_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("content.id"), nullable=False)
    concept_id: Mapped[str] = mapped_column(String(50), nullable=False)
    sentences: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[SentenceFramingFlagStatus] = mapped_column(
        Enum(SentenceFramingFlagStatus, name="sentenceframingflagstatus"),
        nullable=False,
        default=SentenceFramingFlagStatus.pending,
    )
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
