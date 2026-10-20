"""Turn an (already human-approved) concept-map JSON into draft content.

The JSON is the blueprint distilled from the reference pages — original topic
names + one-line scopes + difficulty + olympiad question styles. This creates
the subject/chapter/concepts (resolving prerequisites by title) and runs the
generator per concept. The reference scans are never read here; only these
approved concept descriptions drive generation.
"""
from __future__ import annotations

import uuid
from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.curriculum import Chapter, Concept, Subject
from app.pipeline.run import build_concept

_SUBJECT_NAMES = {"evs": "EVS", "maths": "Maths"}


async def _get_or_create_subject(db: AsyncSession, code: str, grade: int) -> Subject:
    existing = (await db.execute(select(Subject).where(Subject.code == code))).scalar_one_or_none()
    if existing is not None:
        return existing
    subject = Subject(id=uuid.uuid4(), name=_SUBJECT_NAMES.get(code, code.upper()), code=code, grade=grade)
    db.add(subject)
    await db.flush()
    return subject


async def seed_concepts(db: AsyncSession, mapping: dict) -> tuple[Subject, Chapter, list[Concept]]:
    subject = await _get_or_create_subject(db, mapping["subject"], int(mapping.get("grade", 4)))
    chapter = Chapter(id=uuid.uuid4(), subject_id=subject.id, title=mapping["chapter"], order_index=0)
    db.add(chapter)
    await db.flush()

    concepts: list[Concept] = []
    for i, c in enumerate(mapping["concepts"]):
        concept = Concept(id=uuid.uuid4(), chapter_id=chapter.id, title=c["title"], order_index=i, prerequisites=[])
        db.add(concept)
        concepts.append(concept)
    await db.flush()

    by_title = {c.title: c for c in concepts}
    for src, concept in zip(mapping["concepts"], concepts):
        concept.prerequisites = [str(by_title[t].id) for t in src.get("prerequisites", []) if t in by_title]
    await db.commit()
    return subject, chapter, concepts


async def generate_map(
    db: AsyncSession, mapping: dict, *, only: list[str] | None = None, log: Callable[[str], None] = print
) -> dict:
    subject, chapter, concepts = await seed_concepts(db, mapping)
    by_title_src = {c["title"]: c for c in mapping["concepts"]}

    results = []
    for concept in concepts:
        if only and concept.title not in only:
            continue
        src = by_title_src[concept.title]
        band = int(src.get("difficulty_band", 2))
        log(f"Generating: {concept.title} (band {band})")
        results.append(
            await build_concept(
                db,
                concept_id=str(concept.id),
                title=concept.title,
                subject_code=subject.code,
                band=band,
                description=src.get("scope", ""),
                question_styles=src.get("question_styles"),
                log=log,
            )
        )
    return {"chapter_id": str(chapter.id), "concepts": len(concepts), "generated": len(results)}
