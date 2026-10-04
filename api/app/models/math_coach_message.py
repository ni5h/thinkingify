import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class MathCoachMessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"


class MathCoachMessage(Base, TimestampMixin):
    """One turn in the Socratic maths coach's chat for a single problem.

    Mirrors CompanionMessage exactly, but keyed on `math_problem_id`
    instead of `content_id` — the maths coach has no dependency on the
    Content/blog machinery. `session_id` is a plain client-generated UUID
    (one per problem-solving visit, no session table), same design as the
    writing companion. The assessment fields are populated on assistant
    rows only and re-derived by scanning the session each request, not
    tracked as running counters.
    """

    __tablename__ = "math_coach_messages"
    __table_args__ = (
        Index("ix_math_coach_messages_problem_user_created", "math_problem_id", "user_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    math_problem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("math_problems.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    role: Mapped[MathCoachMessageRole] = mapped_column(
        Enum(MathCoachMessageRole, name="mathcoachmessagerole", schema="thinkingify"), nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    ladder_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    asked_for_answer: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    answer_leak_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_fallback: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
