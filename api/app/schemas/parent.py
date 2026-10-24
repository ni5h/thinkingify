import uuid
from datetime import datetime

from pydantic import BaseModel


class ActivityIn(BaseModel):
    concept_id: uuid.UUID | None = None
    context: str = "learn"
    seconds: int


class ChildOut(BaseModel):
    id: uuid.UUID
    name: str


class ConceptStateOut(BaseModel):
    concept_id: uuid.UUID
    title: str
    state: str  # learning | solid | needs_look
    working_at: str | None  # comfortable | stretching | null — never a score


class ChapterStateOut(BaseModel):
    chapter_id: uuid.UUID
    subject: str
    title: str
    concepts: list[ConceptStateOut]


class RecentOut(BaseModel):
    concept_title: str
    when: datetime


class OverviewOut(BaseModel):
    child: ChildOut
    time_this_week_minutes: int
    solid_count: int
    total_concepts: int
    chapters: list[ChapterStateOut]
    recent: list[RecentOut]


class DigestOut(BaseModel):
    lines: list[str]
