import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class MathProblemStatus(str, enum.Enum):
    draft = "draft"
    published = "published"


class MathAnswerKind(str, enum.Enum):
    integer = "integer"
    text = "text"


class MathProblem(Base, TimestampMixin):
    """One admin-authored maths problem the kid solves with the Socratic
    coach. Mirrors Topic's draft/published/soft-delete lifecycle.

    `answer` and `solution_markdown` are HIDDEN — they exist on the model
    and are fed to the coach's system prompt as private context, but the
    public read schemas (MathProblemOut/MathProblemListItem) omit them
    entirely, and the coach's leak guards keep them out of replies. The
    solution is only ever revealed to the kid *after* they solve it.
    """

    __tablename__ = "math_problems"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    statement_markdown: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # Hidden — never in a public schema.
    answer: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    answer_kind: Mapped[MathAnswerKind] = mapped_column(
        Enum(MathAnswerKind, name="mathanswerkind"), nullable=False, default=MathAnswerKind.integer
    )
    # Hidden — the coach's private context, and the post-solve reveal.
    solution_markdown: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # Plain JSON list, not a Theme/Tag table — same "no DB enum, sqlite
    # test compat, filtering is client-side" reasoning as Topic.themes.
    concept_tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list, server_default="[]")
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[MathProblemStatus] = mapped_column(
        Enum(MathProblemStatus, name="mathproblemstatus"), nullable=False, default=MathProblemStatus.draft
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
