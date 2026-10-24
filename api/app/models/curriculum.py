"""The Class 4 pilot concept map: subject → chapter → concept, with skills,
assets, items and book maps hanging off it, plus per-child mastery and writing.

Follows the codebase conventions: all tables live in the `thinkingify` schema
(via Base.metadata), enums are schema-qualified, list-valued fields are JSON
(no association tables / ORM relationships anywhere in this app), and links are
plain FK or JSON-id-list columns. `item`/`asset` carry the review lifecycle
(draft → reviewed → live → retired); learners only ever see `live`.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class CurriculumStatus(str, enum.Enum):
    draft = "draft"
    reviewed = "reviewed"
    live = "live"
    retired = "retired"


class AssetKind(str, enum.Enum):
    audio = "audio"
    script = "script"
    visual = "visual"
    # A Learn card: one idea (title + 1–2 sentences + think-first question +
    # audio script + visual brief), held in `data`; ordered within its concept.
    card = "card"
    # The session wrap-up (3–4 recap lines + one "remember" line), in `data`.
    recap = "recap"


class ItemKind(str, enum.Enum):
    recall = "recall"
    apply = "apply"
    explain = "explain"
    spot_the_mistake = "spot_the_mistake"
    puzzle = "puzzle"


class WritingKind(str, enum.Enum):
    explain = "explain"
    recall = "recall"


class AnswerResult(str, enum.Enum):
    right = "right"
    wrong = "wrong"
    unsure = "unsure"  # never counts as a wrong answer


class Subject(Base, TimestampMixin):
    __tablename__ = "subjects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)  # "maths" | "evs"
    grade: Mapped[int] = mapped_column(Integer, nullable=False, default=4)


class Chapter(Base, TimestampMixin):
    __tablename__ = "chapters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Our chapter maps to one or more of the child's textbook chapters.
    book_refs: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list, server_default="[]")


class Concept(Base, TimestampMixin):
    __tablename__ = "concepts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chapter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("chapters.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Concept ids this concept depends on (JSON list of uuid strings). No DB-level
    # FK integrity — the cycle check + validation live in curriculum_service.
    prerequisites: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list, server_default="[]")


class Skill(Base, TimestampMixin):
    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # 1–4


class Asset(Base, TimestampMixin):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    concept_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("concepts.id"), nullable=False)
    kind: Mapped[AssetKind] = mapped_column(Enum(AssetKind, name="assetkind", schema="thinkingify"), nullable=False)
    # script → body; audio/visual → url. card/recap → structured `data`.
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    # Ordering within a concept (card sequence). Structured payload for card /
    # recap kinds (title, text, visual_brief, audio_script, think, recap lines).
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Cosine similarity to the nearest other generated item / private reference,
    # written by the dedupe pass. Null until deduped.
    dedupe_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[CurriculumStatus] = mapped_column(
        Enum(CurriculumStatus, name="curriculumstatus", schema="thinkingify"),
        nullable=False,
        default=CurriculumStatus.draft,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Item(Base, TimestampMixin):
    __tablename__ = "items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    concept_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("concepts.id"), nullable=False)
    skill_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("skills.id"), nullable=True)
    kind: Mapped[ItemKind] = mapped_column(Enum(ItemKind, name="itemkind", schema="thinkingify"), nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    answer_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Multiple-choice options for check questions (list of strings); the
    # correct one is `answer_key`. Null for free-response items.
    options: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # One-line nudge shown on a wrong answer (never a score), and the card this
    # question came from (a "peek at the source card").
    hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id"), nullable=True
    )
    dedupe_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[CurriculumStatus] = mapped_column(
        Enum(CurriculumStatus, name="curriculumstatus", schema="thinkingify"),
        nullable=False,
        default=CurriculumStatus.draft,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BookMap(Base, TimestampMixin):
    """Metadata only — lets a parent pick their child's book + exam chapters."""

    __tablename__ = "book_maps"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    book: Mapped[str] = mapped_column(String(255), nullable=False)
    chapter_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    concept_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list, server_default="[]")


class Mastery(Base, TimestampMixin):
    """Per-child concept mastery, measured against the child's own baseline
    (populated in Phase 3; table created now to prove the shape)."""

    __tablename__ = "mastery"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    concept_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("concepts.id"), nullable=False)
    baseline: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # "learning" | "solid" | "needs_look". mastered_at is set the first time the
    # concept reaches "solid" and never cleared, so a later demotion to
    # "needs_look" never re-locks concepts that depend on this one.
    state: Mapped[str | None] = mapped_column(String(30), nullable=True)
    mastered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Writing(Base, TimestampMixin):
    """Per-child explanation/recall writing (populated in Phase 4)."""

    __tablename__ = "writing"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    concept_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("concepts.id"), nullable=False)
    kind: Mapped[WritingKind] = mapped_column(Enum(WritingKind, name="writingkind", schema="thinkingify"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)


class AnswerEvent(Base, TimestampMixin):
    """One graded answer. Logged for every answer from day one (with the item's
    difficulty at the time) so the staircase can later be replaced by Elo/BKT.
    The child never sees any of this."""

    __tablename__ = "answer_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("items.id"), nullable=False)
    concept_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("concepts.id"), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    result: Mapped[AnswerResult] = mapped_column(
        Enum(AnswerResult, name="answerresult", schema="thinkingify"), nullable=False
    )
    hint_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    ms: Mapped[int | None] = mapped_column(Integer, nullable=True)


class PracticeSession(Base, TimestampMixin):
    """Server-side quick-check state (the staircase level/streaks the child must
    never see). `check` is the normal run; `challenge` is the 3-item "I already
    know this" skip test."""

    __tablename__ = "practice_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    concept_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("concepts.id"), nullable=False)
    mode: Mapped[str] = mapped_column(String(20), nullable=False, default="check")
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    start_level: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    up_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    miss_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    asked_item_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list, server_default="[]")
    answered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    right_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")


class ActivityEvent(Base, TimestampMixin):
    """Active time a child spent on task, reported by the client in seconds, so
    a parent can see time-on-task per day/week. One row per session segment."""

    __tablename__ = "activity_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    concept_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("concepts.id"), nullable=True)
    context: Mapped[str] = mapped_column(String(20), nullable=False, default="learn")  # learn | check | write
    seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
