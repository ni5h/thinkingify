import pytest
from fastapi import HTTPException

from app.models.curriculum import CurriculumStatus, ItemKind
from app.schemas.curriculum import (
    ChapterCreate,
    ConceptCreate,
    ConceptUpdate,
    ItemCreate,
    SubjectCreate,
)
from app.services import curriculum_service as svc


async def _concept(db, title="C", prerequisites=None):
    subject = await svc.create_subject(db, SubjectCreate(name="Maths", code=f"m-{title}", grade=4))
    chapter = await svc.create_chapter(db, ChapterCreate(subject_id=subject.id, title="Ch"))
    return await svc.create_concept(
        db, ConceptCreate(chapter_id=chapter.id, title=title, prerequisites=prerequisites or [])
    )


async def test_create_tree(db):
    concept = await _concept(db, title="Place value")
    assert concept.title == "Place value"
    assert concept.prerequisites == []


async def test_item_lifecycle_legal(db):
    concept = await _concept(db)
    item = await svc.create_item(db, ItemCreate(concept_id=concept.id, kind=ItemKind.apply, body="2+2?"))
    assert item.status == CurriculumStatus.draft
    item = await svc.transition(db, item, "submit_for_review")
    assert item.status == CurriculumStatus.reviewed
    item = await svc.transition(db, item, "accept")
    assert item.status == CurriculumStatus.live
    item = await svc.transition(db, item, "retire")
    assert item.status == CurriculumStatus.retired


async def test_item_illegal_transition_409(db):
    concept = await _concept(db)
    item = await svc.create_item(db, ItemCreate(concept_id=concept.id, kind=ItemKind.apply, body="x"))
    with pytest.raises(HTTPException) as exc:
        await svc.transition(db, item, "accept")  # accept requires reviewed, not draft
    assert exc.value.status_code == 409


async def test_prereq_self_reference_rejected(db):
    concept = await _concept(db, title="A")
    with pytest.raises(HTTPException) as exc:
        await svc.update_concept(db, concept, ConceptUpdate(prerequisites=[concept.id]))
    assert exc.value.status_code == 400


async def test_prereq_cycle_rejected(db):
    a = await _concept(db, title="A")
    # B requires A
    b = await svc.create_concept(
        db, ConceptCreate(chapter_id=a.chapter_id, title="B", prerequisites=[a.id])
    )
    # Now make A require B -> A->B->A cycle
    with pytest.raises(HTTPException) as exc:
        await svc.update_concept(db, a, ConceptUpdate(prerequisites=[b.id]))
    assert exc.value.status_code == 400


async def test_unknown_prerequisite_rejected(db):
    import uuid

    concept = await _concept(db, title="A")
    with pytest.raises(HTTPException) as exc:
        await svc.update_concept(db, concept, ConceptUpdate(prerequisites=[uuid.uuid4()]))
    assert exc.value.status_code == 400


async def test_learner_reads_live_only(db):
    concept = await _concept(db)
    item = await svc.create_item(db, ItemCreate(concept_id=concept.id, kind=ItemKind.recall, body="q"))
    assert await svc.list_live_items(db, concept.id) == []  # draft hidden
    await svc.transition(db, item, "submit_for_review")
    await svc.transition(db, item, "accept")
    live = await svc.list_live_items(db, concept.id)
    assert [i.id for i in live] == [item.id]
