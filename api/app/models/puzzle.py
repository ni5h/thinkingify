import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class PuzzleTier(str, enum.Enum):
    trial = "trial"
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"
    pro = "pro"


TIER_ORDER: list[PuzzleTier] = [
    PuzzleTier.trial,
    PuzzleTier.beginner,
    PuzzleTier.intermediate,
    PuzzleTier.advanced,
    PuzzleTier.pro,
]


def next_tier(tier: PuzzleTier) -> PuzzleTier | None:
    i = TIER_ORDER.index(tier)
    return TIER_ORDER[i + 1] if i + 1 < len(TIER_ORDER) else None


class PuzzleGameProgress(Base, TimestampMixin):
    __tablename__ = "puzzle_game_progress"
    __table_args__ = (UniqueConstraint("user_id", "game_id", name="uq_puzzle_game_progress_user_game"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    # Plain string, not an enum — more games are coming and a Postgres enum
    # would need an ALTER TYPE for each one; validity is enforced in the
    # service layer instead.
    game_id: Mapped[str] = mapped_column(String(50), nullable=False)
    current_tier: Mapped[PuzzleTier] = mapped_column(
        Enum(PuzzleTier, name="puzzletier"), nullable=False, default=PuzzleTier.trial
    )
    variations_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Ratchet-only high-water mark, separate from current_tier so a future
    # "replay an earlier tier" feature can move current_tier backward
    # without losing the true highest point reached.
    highest_tier_unlocked: Mapped[PuzzleTier] = mapped_column(
        Enum(PuzzleTier, name="puzzletier"), nullable=False, default=PuzzleTier.trial
    )


class PuzzleAttempt(Base, TimestampMixin):
    __tablename__ = "puzzle_attempts"
    __table_args__ = (
        Index("ix_puzzle_attempts_user_game_created", "user_id", "game_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    game_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    tier: Mapped[PuzzleTier] = mapped_column(Enum(PuzzleTier, name="puzzletier"), nullable=False)
    variation_index: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    time_taken_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    # Server-computed from time_taken_ms vs. the tier's target time — never
    # trusted from the client. See puzzle_service.record_attempt().
    beat_time_limit: Mapped[bool] = mapped_column(Boolean, nullable=False)
