import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class GrammarFlagStatus(str, enum.Enum):
    pending = "pending"
    self_corrected = "self_corrected"
    kept_as_is = "kept_as_is"


class GrammarFlag(Base, TimestampMixin):
    """One flagged sentence for one draft, keyed by (content_id,
    concept_id, sentence) — grammar issues are per-sentence-instance, not
    per-word like SpellingFlag: the same concept can legitimately flag
    several different sentences independently, so dedup has to include
    the sentence text, not just the concept.

    No hint/suggested_correction columns, unlike SpellingFlag — that
    content (rule + example pairs) is entirely a function of concept_id
    alone, so it's resolved from grammar_concepts.py at response-assembly
    time instead of being duplicated per row.
    """

    __tablename__ = "grammar_flags"
    __table_args__ = (
        UniqueConstraint("content_id", "concept_id", "sentence", name="uq_grammar_flags_content_concept_sentence"),
        Index("ix_grammar_flags_content_status", "content_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("content.id"), nullable=False)
    concept_id: Mapped[str] = mapped_column(String(50), nullable=False)
    sentence: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[GrammarFlagStatus] = mapped_column(
        Enum(GrammarFlagStatus, name="grammarflagstatus"), nullable=False, default=GrammarFlagStatus.pending
    )
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
