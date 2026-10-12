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
    answer_key: str | None
    status: CurriculumStatus
    updated_at: datetime


class ItemPublicOut(BaseModel):
    """Learner view — never exposes answer_key (same schema-omission guard as
    MathProblemOut dropping answer/solution)."""

    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    concept_id: uuid.UUID
    skill_id: uuid.UUID | None
    kind: ItemKind
    difficulty: int
    body: str


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
