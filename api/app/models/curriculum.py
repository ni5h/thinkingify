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

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text
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


class ItemKind(str, enum.Enum):
    recall = "recall"
    apply = "apply"
    explain = "explain"
    spot_the_mistake = "spot_the_mistake"
    puzzle = "puzzle"


class WritingKind(str, enum.Enum):
    explain = "explain"
    recall = "recall"


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
    # script → body; audio/visual → url.
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
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
    state: Mapped[str | None] = mapped_column(String(30), nullable=True)


class Writing(Base, TimestampMixin):
    """Per-child explanation/recall writing (populated in Phase 4)."""

    __tablename__ = "writing"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    concept_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("concepts.id"), nullable=False)
    kind: Mapped[WritingKind] = mapped_column(Enum(WritingKind, name="writingkind", schema="thinkingify"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
