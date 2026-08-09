import uuid

from sqlalchemy import Boolean, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class MathAttempt(Base, TimestampMixin):
    """One answer submission for a maths problem. `is_correct` is always
    server-computed (compared against the hidden MathProblem.answer) —
    never trusted from the client, unlike Kakooma which trusts a
    client-sent `correct` bool for its speed drills.
    """

    __tablename__ = "math_attempts"
    __table_args__ = (Index("ix_math_attempts_problem_user_created", "math_problem_id", "user_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    math_problem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("math_problems.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    submitted_answer: Mapped[str] = mapped_column(String(255), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
