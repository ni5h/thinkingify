import uuid

from sqlalchemy import select

from app.models.curriculum import (
    AnswerEvent,
    AnswerResult,
    Chapter,
    Concept,
    CurriculumStatus,
    Item,
    ItemKind,
    PracticeSession,
    Subject,
)
from app.services import adaptive_service
from app.services.adaptive_service import apply_result, placement


async def _concept_with_items(db, difficulties: list[int]) -> tuple[Concept, list[Item]]:
    subject = Subject(id=uuid.uuid4(), name="M", code="m" + uuid.uuid4().hex[:6], grade=4)
    db.add(subject)
    await db.flush()
    chapter = Chapter(id=uuid.uuid4(), subject_id=subject.id, title="C", order_index=0)
    db.add(chapter)
    await db.flush()
    concept = Concept(id=uuid.uuid4(), chapter_id=chapter.id, title="Concept", order_index=0, prerequisites=[])
    db.add(concept)
    await db.flush()
    items = []
    for i, d in enumerate(difficulties):
        item = Item(
            id=uuid.uuid4(), concept_id=concept.id, kind=ItemKind.recall, difficulty=d,
            body=f"Q{i} level {d}", options=["A", "B"], answer_key="A", hint=f"hint{i}",
            status=CurriculumStatus.live,
        )
        db.add(item)
        items.append(item)
    await db.commit()
    return concept, items


def test_placement_scales_with_think_rights():
    assert placement([]) == 2
    assert placement(["wrong", "wrong", "wrong"]) == 1
    assert placement(["right", "right", "right", "right"]) == 5
    assert placement(["right", "wrong"]) == 3


def test_staircase_up_on_two_clean_rights_down_on_unsure_or_two_wrongs():
    s = PracticeSession(level=2, up_streak=0, miss_streak=0)
    apply_result(s, "right", False)
    assert s.level == 2  # one right, no move
    apply_result(s, "right", False)
    assert s.level == 3  # two in a row → up
    apply_result(s, "unsure", False)
    assert s.level == 2  # "not sure" → gentle down
    apply_result(s, "wrong", False)
    assert s.level == 2  # a single slip never moves much
    apply_result(s, "wrong", False)
    assert s.level == 1  # two wrongs → down


def test_hint_assisted_right_is_neutral_half_credit():
    s = PracticeSession(level=3, up_streak=1, miss_streak=0)
    apply_result(s, "right", True)
    assert s.level == 3 and s.up_streak == 0


async def test_answer_grades_right_and_logs_event_with_level(db, learner_user):
    concept, items = await _concept_with_items(db, [2, 2, 2, 2, 2])
    session, first = await adaptive_service.start(db, learner_user, concept.id, think_results=[], mode="check")
    out = await adaptive_service.answer(
        db, learner_user, session, item_id=first.id, choice="A", unsure=False, hint_used=False, ms=900
    )
    assert out["correct"] is True and out["reveal_answer"] == "A"
    events = (await db.execute(select(AnswerEvent).where(AnswerEvent.child_id == learner_user.id))).scalars().all()
    assert len(events) == 1 and events[0].level == 2


async def test_wrong_answer_returns_hint_and_source_card_never_a_score(db, learner_user):
    concept, items = await _concept_with_items(db, [2, 2])
    session, first = await adaptive_service.start(db, learner_user, concept.id, think_results=[], mode="check")
    out = await adaptive_service.answer(
        db, learner_user, session, item_id=first.id, choice="B", unsure=False, hint_used=False, ms=None
    )
    assert out["correct"] is False
    assert out["hint"] is not None
    assert "score" not in out and "level" not in out


async def test_unsure_is_logged_as_unsure_not_wrong(db, learner_user):
    concept, items = await _concept_with_items(db, [2, 2])
    session, first = await adaptive_service.start(db, learner_user, concept.id, think_results=[], mode="check")
    out = await adaptive_service.answer(
        db, learner_user, session, item_id=first.id, choice=None, unsure=True, hint_used=False, ms=None
    )
    assert out["unsure"] is True and out["correct"] is False
    event = (await db.execute(select(AnswerEvent))).scalars().first()
    assert event.result == AnswerResult.unsure


async def test_challenge_skip_requires_two_of_three(db, learner_user):
    concept, items = await _concept_with_items(db, [1, 2, 3, 4, 5])
    session, item = await adaptive_service.start(db, learner_user, concept.id, think_results=[], mode="challenge")
    assert session.total == 3
    choices = ["A", "A", "B"]  # two right, one wrong
    out = None
    for i in range(3):
        out = await adaptive_service.answer(
            db, learner_user, session, item_id=item.id, choice=choices[i], unsure=False, hint_used=False, ms=None
        )
        item = out["next_item"]
    assert out["done"] is True and out["skip_earned"] is True
