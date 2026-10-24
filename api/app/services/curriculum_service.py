"""Service layer for the concept map. CRUD for the structural entities plus the
item/asset review lifecycle (draft → reviewed → live → retired, 409 on illegal),
the concept prerequisite cycle check (400), and learner-facing reads that only
ever return `live` content.
"""

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.curriculum import (
    Asset,
    BookMap,
    Chapter,
    Concept,
    CurriculumStatus,
    Item,
    Skill,
    Subject,
)

# Shared lifecycle for item + asset.
_TRANSITIONS: dict[str, tuple[CurriculumStatus, CurriculumStatus]] = {
    "submit_for_review": (CurriculumStatus.draft, CurriculumStatus.reviewed),
    "accept": (CurriculumStatus.reviewed, CurriculumStatus.live),
    "back_to_draft": (CurriculumStatus.reviewed, CurriculumStatus.draft),
    "retire": (CurriculumStatus.live, CurriculumStatus.retired),
    "restore": (CurriculumStatus.retired, CurriculumStatus.draft),
}


def _ids_to_str(ids: list[uuid.UUID] | None) -> list[str] | None:
    return None if ids is None else [str(i) for i in ids]


# --- Subject ---


async def create_subject(db: AsyncSession, data) -> Subject:
    subject = Subject(id=uuid.uuid4(), name=data.name, code=data.code, grade=data.grade)
    db.add(subject)
    await db.commit()
    await db.refresh(subject)
    return subject


async def list_subjects(db: AsyncSession) -> list[Subject]:
    result = await db.execute(select(Subject).order_by(Subject.code))
    return list(result.scalars().all())


async def get_subject(db: AsyncSession, subject_id: uuid.UUID) -> Subject | None:
    return (await db.execute(select(Subject).where(Subject.id == subject_id))).scalar_one_or_none()


async def update_subject(db: AsyncSession, subject: Subject, data) -> Subject:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(subject, field, value)
    await db.commit()
    await db.refresh(subject)
    return subject


# --- Chapter ---


async def create_chapter(db: AsyncSession, data) -> Chapter:
    chapter = Chapter(
        id=uuid.uuid4(),
        subject_id=data.subject_id,
        title=data.title,
        order_index=data.order_index,
        book_refs=list(data.book_refs),
    )
    db.add(chapter)
    await db.commit()
    await db.refresh(chapter)
    return chapter


async def list_chapters(db: AsyncSession, subject_id: uuid.UUID | None = None) -> list[Chapter]:
    stmt = select(Chapter).order_by(Chapter.order_index, Chapter.title)
    if subject_id is not None:
        stmt = stmt.where(Chapter.subject_id == subject_id)
    return list((await db.execute(stmt)).scalars().all())


async def get_chapter(db: AsyncSession, chapter_id: uuid.UUID) -> Chapter | None:
    return (await db.execute(select(Chapter).where(Chapter.id == chapter_id))).scalar_one_or_none()


async def update_chapter(db: AsyncSession, chapter: Chapter, data) -> Chapter:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(chapter, field, value)
    await db.commit()
    await db.refresh(chapter)
    return chapter


# --- Concept (+ prerequisite cycle check) ---


async def _assert_no_prereq_cycle(
    db: AsyncSession, concept_id: uuid.UUID | None, prerequisites: list[uuid.UUID]
) -> None:
    prereq_strs = [str(p) for p in prerequisites]
    if concept_id is not None and str(concept_id) in prereq_strs:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A concept can't require itself.")

    # Build the existing concept→prerequisites graph, then check whether any
    # proposed prerequisite can already reach this concept (which would make a
    # cycle once we add concept→prereq edges).
    rows = (await db.execute(select(Concept.id, Concept.prerequisites))).all()
    graph: dict[str, list[str]] = {str(cid): list(pre or []) for cid, pre in rows}
    # Validate prerequisite ids exist.
    for p in prereq_strs:
        if p not in graph:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown prerequisite concept.")

    if concept_id is None:
        return
    target = str(concept_id)

    def reaches_target(start: str) -> bool:
        seen: set[str] = set()
        stack = [start]
        while stack:
            node = stack.pop()
            if node == target:
                return True
            if node in seen:
                continue
            seen.add(node)
            stack.extend(graph.get(node, []))
        return False

    if any(reaches_target(p) for p in prereq_strs):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="These prerequisites would create a cycle."
        )


async def create_concept(db: AsyncSession, data) -> Concept:
    await _assert_no_prereq_cycle(db, None, data.prerequisites)
    concept = Concept(
        id=uuid.uuid4(),
        chapter_id=data.chapter_id,
        title=data.title,
        order_index=data.order_index,
        prerequisites=[str(p) for p in data.prerequisites],
    )
    db.add(concept)
    await db.commit()
    await db.refresh(concept)
    return concept


async def list_concepts(db: AsyncSession, chapter_id: uuid.UUID | None = None) -> list[Concept]:
    stmt = select(Concept).order_by(Concept.order_index, Concept.title)
    if chapter_id is not None:
        stmt = stmt.where(Concept.chapter_id == chapter_id)
    return list((await db.execute(stmt)).scalars().all())


async def get_concept(db: AsyncSession, concept_id: uuid.UUID) -> Concept | None:
    return (await db.execute(select(Concept).where(Concept.id == concept_id))).scalar_one_or_none()


async def update_concept(db: AsyncSession, concept: Concept, data) -> Concept:
    changes = data.model_dump(exclude_unset=True)
    if "prerequisites" in changes:
        await _assert_no_prereq_cycle(db, concept.id, data.prerequisites or [])
        changes["prerequisites"] = _ids_to_str(data.prerequisites) or []
    for field, value in changes.items():
        setattr(concept, field, value)
    await db.commit()
    await db.refresh(concept)
    return concept


# --- Skill ---


async def create_skill(db: AsyncSession, data) -> Skill:
    skill = Skill(id=uuid.uuid4(), subject_id=data.subject_id, name=data.name, level=data.level)
    db.add(skill)
    await db.commit()
    await db.refresh(skill)
    return skill


async def list_skills(db: AsyncSession, subject_id: uuid.UUID | None = None) -> list[Skill]:
    stmt = select(Skill).order_by(Skill.level, Skill.name)
    if subject_id is not None:
        stmt = stmt.where(Skill.subject_id == subject_id)
    return list((await db.execute(stmt)).scalars().all())


async def get_skill(db: AsyncSession, skill_id: uuid.UUID) -> Skill | None:
    return (await db.execute(select(Skill).where(Skill.id == skill_id))).scalar_one_or_none()


async def update_skill(db: AsyncSession, skill: Skill, data) -> Skill:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(skill, field, value)
    await db.commit()
    await db.refresh(skill)
    return skill


# --- Asset ---


async def create_asset(db: AsyncSession, data) -> Asset:
    asset = Asset(id=uuid.uuid4(), concept_id=data.concept_id, kind=data.kind, body=data.body, url=data.url)
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset


async def get_asset(db: AsyncSession, asset_id: uuid.UUID) -> Asset | None:
    return (
        await db.execute(select(Asset).where(Asset.id == asset_id, Asset.deleted_at.is_(None)))
    ).scalar_one_or_none()


async def update_asset(db: AsyncSession, asset: Asset, data) -> Asset:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(asset, field, value)
    await db.commit()
    await db.refresh(asset)
    return asset


# --- Item ---


async def create_item(db: AsyncSession, data) -> Item:
    item = Item(
        id=uuid.uuid4(),
        concept_id=data.concept_id,
        skill_id=data.skill_id,
        kind=data.kind,
        difficulty=data.difficulty,
        body=data.body,
        answer_key=data.answer_key,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def list_items(
    db: AsyncSession,
    *,
    status_filter: CurriculumStatus | None = None,
    concept_id: uuid.UUID | None = None,
    skill_id: uuid.UUID | None = None,
    kind=None,
) -> list[Item]:
    stmt = select(Item).where(Item.deleted_at.is_(None)).order_by(Item.updated_at.desc())
    if status_filter is not None:
        stmt = stmt.where(Item.status == status_filter)
    if concept_id is not None:
        stmt = stmt.where(Item.concept_id == concept_id)
    if skill_id is not None:
        stmt = stmt.where(Item.skill_id == skill_id)
    if kind is not None:
        stmt = stmt.where(Item.kind == kind)
    return list((await db.execute(stmt)).scalars().all())


async def get_item(db: AsyncSession, item_id: uuid.UUID) -> Item | None:
    return (
        await db.execute(select(Item).where(Item.id == item_id, Item.deleted_at.is_(None)))
    ).scalar_one_or_none()


async def update_item(db: AsyncSession, item: Item, data) -> Item:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.commit()
    await db.refresh(item)
    return item


async def delete_item(db: AsyncSession, item: Item) -> None:
    item.deleted_at = datetime.now(UTC)
    await db.commit()


# --- Shared status transition (item | asset) ---


async def transition(db: AsyncSession, obj: Item | Asset, action: str) -> Item | Asset:
    from_status, to_status = _TRANSITIONS[action]
    if obj.status != from_status:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot {action.replace('_', ' ')} from status '{obj.status.value}'.",
        )
    obj.status = to_status
    await db.commit()
    await db.refresh(obj)
    return obj


# --- BookMap ---


async def create_book_map(db: AsyncSession, data) -> BookMap:
    book_map = BookMap(
        id=uuid.uuid4(),
        book=data.book,
        chapter_ref=data.chapter_ref,
        concept_ids=[str(c) for c in data.concept_ids],
    )
    db.add(book_map)
    await db.commit()
    await db.refresh(book_map)
    return book_map


async def list_book_maps(db: AsyncSession) -> list[BookMap]:
    return list((await db.execute(select(BookMap).order_by(BookMap.book))).scalars().all())


# --- Learner reads (live only) ---


async def list_live_items(db: AsyncSession, concept_id: uuid.UUID) -> list[Item]:
    stmt = select(Item).where(
        Item.concept_id == concept_id,
        Item.status == CurriculumStatus.live,
        Item.deleted_at.is_(None),
    )
    return list((await db.execute(stmt)).scalars().all())


async def list_live_assets(db: AsyncSession, concept_id: uuid.UUID) -> list[Asset]:
    stmt = select(Asset).where(
        Asset.concept_id == concept_id,
        Asset.status == CurriculumStatus.live,
        Asset.deleted_at.is_(None),
    )
    return list((await db.execute(stmt)).scalars().all())


# --- Chapter-level content review + bulk publish ---

_PUBLISHABLE = (CurriculumStatus.draft, CurriculumStatus.reviewed)


def _empty_counts() -> dict[str, int]:
    return {s.value: 0 for s in CurriculumStatus}


async def _chapter_concept_ids(db: AsyncSession, chapter_id: uuid.UUID) -> list[uuid.UUID]:
    rows = await db.execute(select(Concept.id).where(Concept.chapter_id == chapter_id))
    return list(rows.scalars().all())


async def chapter_content_summary(db: AsyncSession, chapter_id: uuid.UUID) -> dict:
    """Per-concept + chapter-total counts of items and assets by status, so an
    admin can see what's draft vs live before publishing a whole chapter."""
    concepts = await list_concepts(db, chapter_id)
    concept_ids = [c.id for c in concepts]

    item_counts: dict[str, dict[str, int]] = {}
    asset_counts: dict[str, dict[str, int]] = {}
    if concept_ids:
        for model, bucket in ((Item, item_counts), (Asset, asset_counts)):
            rows = await db.execute(
                select(model.concept_id, model.status, func.count())
                .where(model.concept_id.in_(concept_ids), model.deleted_at.is_(None))
                .group_by(model.concept_id, model.status)
            )
            for concept_id, st, n in rows.all():
                bucket.setdefault(str(concept_id), _empty_counts())[st.value] = n

    concepts_out: list[dict] = []
    item_totals, asset_totals = _empty_counts(), _empty_counts()
    for c in sorted(concepts, key=lambda x: x.order_index):
        items = item_counts.get(str(c.id), _empty_counts())
        assets = asset_counts.get(str(c.id), _empty_counts())
        for s in CurriculumStatus:
            item_totals[s.value] += items[s.value]
            asset_totals[s.value] += assets[s.value]
        concepts_out.append(
            {"concept_id": c.id, "title": c.title, "order_index": c.order_index, "items": items, "assets": assets}
        )

    publishable = sum(item_totals[s.value] + asset_totals[s.value] for s in _PUBLISHABLE)
    return {
        "concepts": concepts_out,
        "item_totals": item_totals,
        "asset_totals": asset_totals,
        "publishable_count": publishable,
        "live_count": item_totals["live"] + asset_totals["live"],
    }


async def _bulk_set_status(
    db: AsyncSession, chapter_id: uuid.UUID, from_statuses, to_status: CurriculumStatus
) -> dict:
    concept_ids = await _chapter_concept_ids(db, chapter_id)
    if not concept_ids:
        return {"items": 0, "assets": 0}
    counts: dict[str, int] = {}
    for key, model in (("items", Item), ("assets", Asset)):
        result = await db.execute(
            update(model)
            .where(
                model.concept_id.in_(concept_ids),
                model.deleted_at.is_(None),
                model.status.in_(from_statuses),
            )
            .values(status=to_status)
        )
        counts[key] = result.rowcount or 0
    await db.commit()
    return counts


async def publish_chapter(db: AsyncSession, chapter_id: uuid.UUID) -> dict:
    """Promote every draft/reviewed item and asset under the chapter straight to
    live. For a single trusted admin accepting a whole generated chapter — skips
    the per-item reviewed step on purpose."""
    return await _bulk_set_status(db, chapter_id, _PUBLISHABLE, CurriculumStatus.live)


async def retire_chapter(db: AsyncSession, chapter_id: uuid.UUID) -> dict:
    """Pull a chapter's live content back to retired (unpublish)."""
    return await _bulk_set_status(db, chapter_id, (CurriculumStatus.live,), CurriculumStatus.retired)
