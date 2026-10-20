"""Per-concept mastery against the child's own baseline, plus prerequisite
gating. Mirrors brother_service's shape: baseline from the first N attempts,
mastery over a trailing window against an accuracy floor. Retention can demote
"solid" → "needs_look", but `mastered_at` is never cleared, so a demotion never
re-locks a concept that depended on this one.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.curriculum import AnswerEvent, AnswerResult, Concept, Mastery
from app.services.mastery_math import credited_accuracy, median_int

_BASELINE_SAMPLE = 5  # baseline = median ms of the first N answers
_MIN_ATTEMPTS = 5  # graded answers needed before mastery can fire
_WINDOW = 6  # evaluated over the trailing N answers
_ACCURACY_FLOOR = 0.80  # reach this (credited) to become solid
_RETENTION_FLOOR = 0.60  # fall below this and a solid concept needs another look


async def _events(db: AsyncSession, child_id: uuid.UUID, concept_id: uuid.UUID) -> list[AnswerEvent]:
    result = await db.execute(
        select(AnswerEvent)
        .where(AnswerEvent.child_id == child_id, AnswerEvent.concept_id == concept_id)
        .order_by(AnswerEvent.created_at)
    )
    return list(result.scalars().all())


async def get_or_create(db: AsyncSession, child_id: uuid.UUID, concept_id: uuid.UUID) -> Mastery:
    result = await db.execute(
        select(Mastery).where(Mastery.child_id == child_id, Mastery.concept_id == concept_id)
    )
    mastery = result.scalar_one_or_none()
    if mastery is None:
        mastery = Mastery(id=uuid.uuid4(), child_id=child_id, concept_id=concept_id, state="learning")
        db.add(mastery)
        await db.flush()
    return mastery


async def evaluate(db: AsyncSession, child_id: uuid.UUID, concept_id: uuid.UUID) -> Mastery:
    """Recompute mastery from the answer log. Caller owns the commit."""
    events = await _events(db, child_id, concept_id)
    mastery = await get_or_create(db, child_id, concept_id)

    ms_values = [e.ms for e in events if e.ms is not None]
    if mastery.baseline is None and len(ms_values) >= _BASELINE_SAMPLE:
        mastery.baseline = median_int(ms_values[:_BASELINE_SAMPLE])

    graded = [e for e in events if e.result != AnswerResult.unsure]
    if len(graded) < _MIN_ATTEMPTS:
        await db.flush()
        return mastery

    window = events[-_WINDOW:]
    acc = credited_accuracy([e.result.value for e in window], [e.hint_used for e in window])
    if acc is None:
        await db.flush()
        return mastery

    if mastery.state in (None, "learning", "needs_look") and acc >= _ACCURACY_FLOOR:
        mastery.state = "solid"
        if mastery.mastered_at is None:
            mastery.mastered_at = datetime.now(UTC)
    elif mastery.state == "solid" and acc < _RETENTION_FLOOR:
        mastery.state = "needs_look"  # mastered_at kept → never re-locks dependents

    await db.flush()
    return mastery


async def _mastery_map(db: AsyncSession, child_id: uuid.UUID, concept_ids: list[uuid.UUID]) -> dict[str, Mastery]:
    if not concept_ids:
        return {}
    result = await db.execute(
        select(Mastery).where(Mastery.child_id == child_id, Mastery.concept_id.in_(concept_ids))
    )
    return {str(m.concept_id): m for m in result.scalars().all()}


def _is_available(concept: Concept, mastery_by_id: dict[str, Mastery]) -> bool:
    prereqs = concept.prerequisites or []
    if not prereqs:
        return True
    # Available once every prerequisite has *ever* been mastered (mastered_at
    # set), even if one has since slipped to needs_look.
    return all(
        (m := mastery_by_id.get(str(p))) is not None and m.mastered_at is not None for p in prereqs
    )


async def concept_progress(db: AsyncSession, child_id: uuid.UUID, concepts: list[Concept]) -> list[dict]:
    """State + availability for a set of concepts (e.g. a chapter's trail)."""
    ids = [c.id for c in concepts]
    prereq_ids = [uuid.UUID(str(p)) for c in concepts for p in (c.prerequisites or [])]
    mastery_by_id = await _mastery_map(db, child_id, ids + prereq_ids)
    out = []
    for concept in concepts:
        mastery = mastery_by_id.get(str(concept.id))
        out.append(
            {
                "concept_id": concept.id,
                "state": mastery.state if mastery and mastery.state else "learning",
                "available": _is_available(concept, mastery_by_id),
                "mastered": bool(mastery and mastery.mastered_at is not None),
            }
        )
    return out
