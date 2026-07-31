import uuid

from sqlalchemy import JSON, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ParentReport(Base, TimestampMixin):
    """One generated report for one submit/publish event on a Content
    row. No uniqueness on content_id — a kid can be rejected and
    resubmit, and each submission gets its own report so a guardian can
    see how a resubmission changed, not just the latest state.

    went_well/was_tricky/stage_breakdown are JSON (not normalized
    tables) — same precedent as Topic.themes, chosen so the sqlite-backed
    test suite can create this table too; nothing here needs relational
    querying, it's read back as a whole document per report.
    """

    __tablename__ = "parent_reports"
    __table_args__ = (Index("ix_parent_reports_content_created", "content_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("content.id"), nullable=False)
    # Snapshotted at generation time, not derived at read time — a
    # rejected-and-resubmitted piece can have different word counts
    # across its reports, and each report should reflect the draft as it
    # stood at that submission, not the (possibly since-changed) current
    # content_markdown.
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # LLM-generated (one call per report) — fail-soft to templated
    # fallback text if the call fails, see parent_report_service.py.
    headline: Mapped[str] = mapped_column(Text, nullable=False)
    creativity_narrative: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_action: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Templated from logged evaluation-stage/companion data, no LLM.
    went_well: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    was_tricky: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    stage_breakdown: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    ai_help_level: Mapped[str] = mapped_column(Text, nullable=False)
