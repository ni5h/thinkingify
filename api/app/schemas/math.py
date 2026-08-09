import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.math_coach_message import MathCoachMessageRole
from app.models.math_problem import MathAnswerKind, MathProblemStatus


# --- Problem authoring (admin/author path — carries answer + solution) ---


class MathProblemCreate(BaseModel):
    title: str
    statement_markdown: str = ""
    answer: str = ""
    answer_kind: MathAnswerKind = MathAnswerKind.integer
    solution_markdown: str = ""
    concept_tags: list[str] = []
    difficulty: int = 1
    order_index: int = 0


class MathProblemUpdate(BaseModel):
    title: str | None = None
    statement_markdown: str | None = None
    answer: str | None = None
    answer_kind: MathAnswerKind | None = None
    solution_markdown: str | None = None
    concept_tags: list[str] | None = None
    difficulty: int | None = None
    order_index: int | None = None


class MathProblemAdminOut(BaseModel):
    """Full view for the author — includes the hidden answer/solution."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    slug: str
    statement_markdown: str
    answer: str
    answer_kind: MathAnswerKind
    solution_markdown: str
    concept_tags: list[str]
    difficulty: int
    status: MathProblemStatus
    order_index: int
    author_id: uuid.UUID
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


# --- Problem reads (public / kid path — answer + solution deliberately omitted) ---


class MathProblemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    slug: str
    statement_markdown: str
    concept_tags: list[str]
    difficulty: int
    status: MathProblemStatus
    order_index: int


class MathProblemListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    slug: str
    concept_tags: list[str]
    difficulty: int
    order_index: int


# --- Coach chat ---


class MathCoachMessageCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=2000)
    session_id: uuid.UUID


class MathCoachMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    math_problem_id: uuid.UUID
    role: MathCoachMessageRole
    body: str
    ladder_level: int | None
    asked_for_answer: bool
    answer_leak_blocked: bool
    is_fallback: bool
    created_at: datetime


# --- Answer attempts ---


class MathAttemptCreate(BaseModel):
    submitted_answer: str = Field(..., min_length=1, max_length=255)


class MathAttemptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    math_problem_id: uuid.UUID
    submitted_answer: str
    is_correct: bool
    created_at: datetime
    # The worked solution — populated ONLY on a correct attempt (the
    # post-solve payoff), never leaked before the kid has solved it.
    solution_markdown: str | None = None
