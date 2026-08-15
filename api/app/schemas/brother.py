import uuid

from pydantic import BaseModel, Field

from app.models.brother import BrotherTierStatus


class BrotherTierStateOut(BaseModel):
    tier_id: str
    name: str
    status: BrotherTierStatus
    baseline_ms: int | None
    # Derived live from the attempt log, not stored.
    median_ms: int | None
    accuracy: float | None
    attempts_count: int


class BrotherQuestionOut(BaseModel):
    index: int
    tier_id: str
    number: int
    # How many trailing digits are "active" — the client greys the rest
    # (B4/B6). NEVER includes the correct answer.
    active_digits: int


class BrotherSessionOut(BaseModel):
    id: uuid.UUID
    questions: list[BrotherQuestionOut]


class BrotherAnswerCreate(BaseModel):
    index: int = Field(..., ge=0)
    user_answer: int = Field(..., ge=0)
    response_ms: int = Field(..., ge=0)


class BrotherAnswerResultOut(BaseModel):
    correct: bool
    correct_answer: int
    mastered_tier_id: str | None = None
    unlocked_tier_id: str | None = None
