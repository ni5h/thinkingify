import uuid

from app.models.curriculum import AnswerEvent, AnswerResult, Concept
from app.services import concept_mastery_service as cm


async def _log(db, child_id, concept_id, results, ms=1000):
    for r in results:
        db.add(
            AnswerEvent(
                id=uuid.uuid4(), child_id=child_id, concept_id=concept_id, item_id=uuid.uuid4(),
                level=2, result=AnswerResult(r), hint_used=False, ms=ms,
            )
        )
    await db.flush()


async def test_mastery_becomes_solid_and_sets_baseline(db, learner_user):
    cid = uuid.uuid4()
    await _log(db, learner_user.id, cid, ["right"] * 6)
    mastery = await cm.evaluate(db, learner_user.id, cid)
    assert mastery.state == "solid"
    assert mastery.mastered_at is not None
    assert mastery.baseline == 1000  # median ms of the first five answers


async def test_demotion_to_needs_look_keeps_mastered_at(db, learner_user):
    cid = uuid.uuid4()
    await _log(db, learner_user.id, cid, ["right"] * 6)
    await cm.evaluate(db, learner_user.id, cid)
    first_mastered = (await cm.get_or_create(db, learner_user.id, cid)).mastered_at

    await _log(db, learner_user.id, cid, ["wrong"] * 6)
    mastery = await cm.evaluate(db, learner_user.id, cid)
    assert mastery.state == "needs_look"
    assert mastery.mastered_at == first_mastered  # never cleared → never re-locks


async def test_prerequisite_gating_unlocks_and_never_relocks(db, learner_user):
    chapter_id = uuid.uuid4()
    a = Concept(id=uuid.uuid4(), chapter_id=chapter_id, title="A", order_index=0, prerequisites=[])
    b = Concept(id=uuid.uuid4(), chapter_id=chapter_id, title="B", order_index=1, prerequisites=[str(a.id)])
    db.add_all([a, b])
    await db.flush()

    progress = {str(p["concept_id"]): p for p in await cm.concept_progress(db, learner_user.id, [a, b])}
    assert progress[str(b.id)]["available"] is False  # locked until A mastered

    await _log(db, learner_user.id, a.id, ["right"] * 6)
    await cm.evaluate(db, learner_user.id, a.id)
    progress = {str(p["concept_id"]): p for p in await cm.concept_progress(db, learner_user.id, [a, b])}
    assert progress[str(b.id)]["available"] is True

    await _log(db, learner_user.id, a.id, ["wrong"] * 6)
    await cm.evaluate(db, learner_user.id, a.id)
    progress = {str(p["concept_id"]): p for p in await cm.concept_progress(db, learner_user.id, [a, b])}
    assert progress[str(a.id)]["state"] == "needs_look"
    assert progress[str(b.id)]["available"] is True  # demotion of A never re-locks B
