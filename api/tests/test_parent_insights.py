import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.models.curriculum import ActivityEvent, AnswerEvent, AnswerResult, Chapter, Concept, Subject
from app.models.family_link import FamilyLink, FamilyLinkStatus
from app.models.user import User, UserRole
from app.services import concept_mastery_service, parent_insights_service as pins


async def _guardian_and_child(db) -> tuple[User, User]:
    g = User(id=uuid.uuid4(), google_sub="g-" + uuid.uuid4().hex[:6], email=f"{uuid.uuid4().hex[:6]}@x.com", name="Parent", role=UserRole.learner)
    c = User(id=uuid.uuid4(), google_sub="c-" + uuid.uuid4().hex[:6], email=f"{uuid.uuid4().hex[:6]}@x.com", name="Neo", role=UserRole.learner)
    db.add_all([g, c])
    await db.flush()
    db.add(FamilyLink(id=uuid.uuid4(), guardian_id=g.id, child_id=c.id, requested_by=g.id, status=FamilyLinkStatus.accepted))
    await db.commit()
    return g, c


async def _concept(db) -> Concept:
    s = Subject(id=uuid.uuid4(), name="EVS", code="evs" + uuid.uuid4().hex[:4], grade=4)
    db.add(s)
    await db.flush()
    ch = Chapter(id=uuid.uuid4(), subject_id=s.id, title="Animals", order_index=0)
    db.add(ch)
    await db.flush()
    c = Concept(id=uuid.uuid4(), chapter_id=ch.id, title="Animal Groups", order_index=0, prerequisites=[])
    db.add(c)
    await db.commit()
    return c


async def test_list_children_returns_only_linked_child(db):
    g, c = await _guardian_and_child(db)
    children = await pins.list_children(db, g)
    assert [ch.id for ch in children] == [c.id]


async def test_overview_blocks_a_non_guardian(db, learner_user):
    _, c = await _guardian_and_child(db)
    with pytest.raises(HTTPException) as exc:
        await pins.child_overview(db, learner_user, c.id)
    assert exc.value.status_code == 403


async def test_overview_counts_solid_time_and_working_at(db):
    g, c = await _guardian_and_child(db)
    concept = await _concept(db)
    for _ in range(6):
        db.add(AnswerEvent(id=uuid.uuid4(), child_id=c.id, concept_id=concept.id, item_id=uuid.uuid4(), level=2, result=AnswerResult.right, hint_used=False, ms=1000))
    await db.flush()
    await concept_mastery_service.evaluate(db, c.id, concept.id)
    db.add(ActivityEvent(id=uuid.uuid4(), child_id=c.id, concept_id=concept.id, context="learn", seconds=300))
    await db.commit()

    overview = await pins.child_overview(db, g, c.id)
    assert overview["solid_count"] == 1 and overview["total_concepts"] == 1
    assert overview["time_this_week_minutes"] == 5
    state = overview["chapters"][0]["concepts"][0]
    assert state["state"] == "solid"
    assert state["working_at"] == "comfortable"
    assert overview["recent"][0]["concept_title"] == "Animal Groups"


async def test_record_activity_caps_and_ignores_zero(db):
    _, c = await _guardian_and_child(db)
    await pins.record_activity(db, c, concept_id=None, context="learn", seconds=99999)
    await pins.record_activity(db, c, concept_id=None, context="learn", seconds=0)
    rows = (await db.execute(select(ActivityEvent).where(ActivityEvent.child_id == c.id))).scalars().all()
    assert len(rows) == 1 and rows[0].seconds == 3600


async def test_digest_is_calm_and_never_a_score_or_rank(db):
    g, c = await _guardian_and_child(db)
    await _concept(db)
    digest = await pins.child_digest(db, g, c.id)
    blob = " ".join(digest["lines"]).lower()
    assert len(digest["lines"]) >= 2
    assert "score" not in blob and "rank" not in blob
