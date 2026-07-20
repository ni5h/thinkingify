import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.puzzle import PuzzleTier

VARIATIONS_PER_TIER = 10


class GameProgressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    game_id: str
    current_tier: PuzzleTier
    variations_completed: int
    variations_per_tier: int = VARIATIONS_PER_TIER
    highest_tier_unlocked: PuzzleTier
    updated_at: datetime


class AttemptCreate(BaseModel):
    started_at: datetime
    completed_at: datetime
    time_taken_ms: int
    correct: bool


class AttemptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    game_id: str
    tier: PuzzleTier
    variation_index: int
    started_at: datetime
    completed_at: datetime
    time_taken_ms: int
    correct: bool
    beat_time_limit: bool
    created_at: datetime


class AttemptResultOut(BaseModel):
    attempt: AttemptOut
    progress: GameProgressOut
    tier_advanced: bool


class GameStatsOut(BaseModel):
    """Effort-focused, not output-focused: counts and time invested, never
    an accuracy percentage or "best time" — see puzzle_service.get_stats_for_user."""

    game_id: str
    current_tier: PuzzleTier
    total_attempts: int
    attempts_today: int
    attempts_this_week: int  # rolling 7 days, not calendar week
    total_time_ms: int
    last_attempt_at: datetime | None
