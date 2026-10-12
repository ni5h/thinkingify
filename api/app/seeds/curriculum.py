"""Seed the concept-map skeleton for the Class 4 pilot: the two subjects, one
Maths chapter ("Big Numbers") and one EVS chapter, each with a few concepts and
no items/assets yet — just enough to prove the tree shape. Idempotent (keyed on
subject code / chapter title / concept title). Run standalone:

    python -m app.seeds.curriculum
"""

import asyncio
import uuid

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.curriculum import Chapter, Concept, Subject

# subject code -> (name, [(chapter title, book_refs, [concept titles])])
_TREE = {
    "maths": (
        "Maths",
        [
            (
                "Big Numbers",
                ["Chapter 1"],
                ["Reading large numbers", "Place value to lakhs", "Comparing big numbers", "Rounding off"],
            ),
        ],
    ),
    "evs": (
        "EVS",
        [
            (
                "Our Food",
                ["Chapter 1"],
                ["Where food comes from", "Food from plants and animals", "Eating well"],
            ),
        ],
    ),
}


async def _get_or_create_subject(db, code, name) -> Subject:
    subject = (await db.execute(select(Subject).where(Subject.code == code))).scalar_one_or_none()
    if subject is None:
        subject = Subject(id=uuid.uuid4(), name=name, code=code, grade=4)
        db.add(subject)
        await db.commit()
        await db.refresh(subject)
    return subject


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        chapters_created = concepts_created = 0
        for code, (name, chapters) in _TREE.items():
            subject = await _get_or_create_subject(db, code, name)
            for ch_order, (title, book_refs, concept_titles) in enumerate(chapters):
                chapter = (
                    await db.execute(
                        select(Chapter).where(Chapter.subject_id == subject.id, Chapter.title == title)
                    )
                ).scalar_one_or_none()
                if chapter is None:
                    chapter = Chapter(
                        id=uuid.uuid4(),
                        subject_id=subject.id,
                        title=title,
                        order_index=ch_order,
                        book_refs=list(book_refs),
                    )
                    db.add(chapter)
                    await db.commit()
                    await db.refresh(chapter)
                    chapters_created += 1
                for c_order, c_title in enumerate(concept_titles):
                    exists = (
                        await db.execute(
                            select(Concept.id).where(
                                Concept.chapter_id == chapter.id, Concept.title == c_title
                            )
                        )
                    ).scalar_one_or_none()
                    if exists is not None:
                        continue
                    db.add(
                        Concept(
                            id=uuid.uuid4(),
                            chapter_id=chapter.id,
                            title=c_title,
                            order_index=c_order,
                            prerequisites=[],
                        )
                    )
                    concepts_created += 1
                await db.commit()
        print(f"Seeded {chapters_created} chapter(s), {concepts_created} concept(s).")


if __name__ == "__main__":
    asyncio.run(seed())
