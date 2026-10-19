import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.curriculum import AssetKind, CurriculumStatus, ItemKind

# --- Subject ---


class SubjectCreate(BaseModel):
    name: str
    code: str
    grade: int = 4


class SubjectUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    grade: int | None = None


class SubjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    code: str
    grade: int


# --- Chapter ---


class ChapterCreate(BaseModel):
    subject_id: uuid.UUID
    title: str
    order_index: int = 0
    book_refs: list[str] = []


class ChapterUpdate(BaseModel):
    title: str | None = None
    order_index: int | None = None
    book_refs: list[str] | None = None


class ChapterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    subject_id: uuid.UUID
    title: str
    order_index: int
    book_refs: list[str]


# --- Concept ---


class ConceptCreate(BaseModel):
    chapter_id: uuid.UUID
    title: str
    order_index: int = 0
    prerequisites: list[uuid.UUID] = []


class ConceptUpdate(BaseModel):
    title: str | None = None
    order_index: int | None = None
    prerequisites: list[uuid.UUID] | None = None


class ConceptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    chapter_id: uuid.UUID
    title: str
    order_index: int
    prerequisites: list[uuid.UUID]


# --- Skill ---


class SkillCreate(BaseModel):
    subject_id: uuid.UUID
    name: str
    level: int = 1


class SkillUpdate(BaseModel):
    name: str | None = None
    level: int | None = None


class SkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    subject_id: uuid.UUID
    name: str
    level: int


# --- Asset ---


class AssetCreate(BaseModel):
    concept_id: uuid.UUID
    kind: AssetKind
    body: str | None = None
    url: str | None = None


class AssetUpdate(BaseModel):
    body: str | None = None
    url: str | None = None


class AssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    concept_id: uuid.UUID
    kind: AssetKind
    body: str | None
    url: str | None
    order_index: int
    data: dict | None
    status: CurriculumStatus


# --- Item ---


class ItemCreate(BaseModel):
    concept_id: uuid.UUID
    skill_id: uuid.UUID | None = None
    kind: ItemKind
    difficulty: int = 1
    body: str = ""
    answer_key: str | None = None


class ItemUpdate(BaseModel):
    skill_id: uuid.UUID | None = None
    kind: ItemKind | None = None
    difficulty: int | None = None
    body: str | None = None
    answer_key: str | None = None


class ItemOut(BaseModel):
    """Admin view — includes the hidden answer_key."""

    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    concept_id: uuid.UUID
    skill_id: uuid.UUID | None
    kind: ItemKind
    difficulty: int
    body: str
    options: list[str] | None
    answer_key: str | None
    hint: str | None
    source_asset_id: uuid.UUID | None
    dedupe_score: float | None
    status: CurriculumStatus
    updated_at: datetime


class ItemPublicOut(BaseModel):
    """Learner view — never exposes answer_key OR difficulty (the adaptive level
    the child must never see). Grading and the staircase run server-side; the
    hint and source card come back only in the answer response, on a wrong try."""

    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    concept_id: uuid.UUID
    kind: ItemKind
    body: str
    options: list[str] | None


# --- BookMap ---


class BookMapCreate(BaseModel):
    book: str
    chapter_ref: str
    concept_ids: list[uuid.UUID] = []


class BookMapUpdate(BaseModel):
    book: str | None = None
    chapter_ref: str | None = None
    concept_ids: list[uuid.UUID] | None = None


class BookMapOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    book: str
    chapter_ref: str
    concept_ids: list[uuid.UUID]


# --- Learner practice session (Phase 3) ---


class CheckStartIn(BaseModel):
    # Per-card think-first results, used only for placement. "check" is the
    # normal run; "challenge" is the 3-item "I already know this" skip test.
    think_results: list[str] = []  # "right" | "wrong" | "unsure"
    mode: str = "check"


class CheckSessionOut(BaseModel):
    session_id: uuid.UUID
    index: int  # 1-based position of `item` in the run
    total: int
    item: ItemPublicOut | None
    done: bool = False


class AnswerIn(BaseModel):
    item_id: uuid.UUID
    choice: str | None = None
    unsure: bool = False
    hint_used: bool = False
    ms: int | None = None


class AnswerOut(BaseModel):
    # No score, ever. A wrong try returns the hint and the source card to peek.
    correct: bool
    unsure: bool
    reveal_answer: str | None
    hint: str | None
    source_asset_id: uuid.UUID | None
    index: int
    total: int
    done: bool
    next_item: ItemPublicOut | None = None
    skip_earned: bool | None = None  # challenge mode only


class ConceptProgressOut(BaseModel):
    concept_id: uuid.UUID
    state: str  # "learning" | "solid" | "needs_look" — never a number
    available: bool
    mastered: bool
