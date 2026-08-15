import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException

from app.models.brother import BrotherAttempt, BrotherTierStatus
from app.services import brother_service


async def _seed_attempts(db, user, tier_id, specs):
    """specs: list of (response_ms, correct). Explicit monotonic created_at
    so 'first 10' / 'trailing 20' ordering is deterministic in tests."""
    base = datetime(2026, 1, 1, tzinfo=UTC)
    for i, (ms, correct) in enumerate(specs):
        db.add(
            BrotherAttempt(
                id=uuid.uuid4(),
                user_id=user.id,
                tier_id=tier_id,
                number=7,
                correct_answer=3,
                user_answer=3 if correct else 4,
                correct=correct,
                response_ms=ms,
                created_at=base + timedelta(seconds=i),
            )
        )
    await db.commit()


async def test_state_seeds_b1_active_rest_locked(db, learner_user):
    states = await brother_service.get_or_create_state(db, learner_user)
    by_id = {s.tier_id: s.status for s in states}
    assert by_id["B1"] == BrotherTierStatus.active
    assert by_id["B2"] == BrotherTierStatus.locked
    assert by_id["B6"] == BrotherTierStatus.locked
    # Idempotent — second call doesn't duplicate.
    again = await brother_service.get_or_create_state(db, learner_user)
    assert len(again) == 6


async def test_session_issues_ten_active_tier_questions(db, learner_user):
    session = await brother_service.start_session(db, learner_user)
    assert len(session.questions) == 10
    assert all(q["tier_id"] == "B1" for q in session.questions)


async def test_record_answer_checks_correctness_server_side(db, learner_user):
    session = await brother_service.start_session(db, learner_user)
    q = session.questions[0]
    from app.services.brother_tiers import TIERS_BY_ID, brother

    right = brother(q["number"], TIERS_BY_ID[q["tier_id"]].power)

    correct, correct_answer, _, _ = await brother_service.record_answer(
        db, learner_user, session, q["index"], right, 1500
    )
    assert correct is True
    assert correct_answer == right

    q2 = session.questions[1]
    wrong = brother(q2["number"], TIERS_BY_ID[q2["tier_id"]].power) + 1
    correct2, _, _, _ = await brother_service.record_answer(db, learner_user, session, q2["index"], wrong, 1500)
    assert correct2 is False


async def test_record_answer_rejects_re_answer_and_unknown_index(db, learner_user):
    session = await brother_service.start_session(db, learner_user)
    await brother_service.record_answer(db, learner_user, session, 0, 1, 1000)
    with pytest.raises(HTTPException) as exc:
        await brother_service.record_answer(db, learner_user, session, 0, 1, 1000)
    assert exc.value.status_code == 409

    with pytest.raises(HTTPException) as exc:
        await brother_service.record_answer(db, learner_user, session, 999, 1, 1000)
    assert exc.value.status_code == 404


async def test_baseline_set_once_from_first_ten_and_never_recomputed(db, learner_user):
    await brother_service.get_or_create_state(db, learner_user)
    await _seed_attempts(db, learner_user, "B1", [(1000, True)] * 10)
    await brother_service._evaluate(db, learner_user, "B1")
    progress = await brother_service._get_progress(db, learner_user.id, "B1")
    assert progress.baseline_ms == 1000

    # Add much faster attempts; baseline must not move.
    await _seed_attempts(db, learner_user, "B1", [(200, True)] * 5)
    await brother_service._evaluate(db, learner_user, "B1")
    progress = await brother_service._get_progress(db, learner_user.id, "B1")
    assert progress.baseline_ms == 1000


async def test_mastery_fires_on_accuracy_and_speed_and_unlocks_next(db, learner_user):
    await brother_service.get_or_create_state(db, learner_user)
    # First 10 slow+correct -> baseline 1000. Next 20 fast+correct -> the
    # trailing-20 window is all @500 (<= 600) and 100% accurate.
    await _seed_attempts(db, learner_user, "B1", [(1000, True)] * 10 + [(500, True)] * 20)
    mastered, unlocked = await brother_service._evaluate(db, learner_user, "B1")
    assert mastered == "B1"
    assert unlocked == "B2"

    b1 = await brother_service._get_progress(db, learner_user.id, "B1")
    b2 = await brother_service._get_progress(db, learner_user.id, "B2")
    assert b1.status == BrotherTierStatus.mastered
    assert b1.mastered_at is not None
    assert b2.status == BrotherTierStatus.active


async def test_mastery_blocked_by_low_accuracy(db, learner_user):
    await brother_service.get_or_create_state(db, learner_user)
    # Fast enough, but 4 of the trailing 20 are wrong -> 80% < 90%.
    trailing = [(500, True)] * 16 + [(500, False)] * 4
    await _seed_attempts(db, learner_user, "B1", [(1000, True)] * 10 + trailing)
    mastered, unlocked = await brother_service._evaluate(db, learner_user, "B1")
    assert mastered is None and unlocked is None
    b1 = await brother_service._get_progress(db, learner_user.id, "B1")
    assert b1.status == BrotherTierStatus.active


async def test_mastery_blocked_by_slow_speed(db, learner_user):
    await brother_service.get_or_create_state(db, learner_user)
    # Accurate, but median 700 > 60% of the 1000 baseline.
    await _seed_attempts(db, learner_user, "B1", [(1000, True)] * 10 + [(700, True)] * 20)
    mastered, _ = await brother_service._evaluate(db, learner_user, "B1")
    assert mastered is None


async def test_mastery_needs_minimum_attempts(db, learner_user):
    await brother_service.get_or_create_state(db, learner_user)
    # Fast + perfect but only 12 attempts (< 15 minimum).
    await _seed_attempts(db, learner_user, "B1", [(1000, True)] * 10 + [(100, True)] * 2)
    mastered, _ = await brother_service._evaluate(db, learner_user, "B1")
    assert mastered is None


async def test_unlock_is_one_way_no_relock(db, learner_user):
    await brother_service.get_or_create_state(db, learner_user)
    await _seed_attempts(db, learner_user, "B1", [(1000, True)] * 10 + [(500, True)] * 20)
    await brother_service._evaluate(db, learner_user, "B1")
    # Re-evaluating a mastered tier is a no-op and never re-locks B2.
    mastered, unlocked = await brother_service._evaluate(db, learner_user, "B1")
    assert mastered is None and unlocked is None
    b2 = await brother_service._get_progress(db, learner_user.id, "B2")
    assert b2.status == BrotherTierStatus.active


def _token_for(user, role: str) -> str:
    from app.core.security import create_access_token

    return create_access_token(str(user.id), email=user.email, name=user.name, role=role)


async def test_routes_require_auth(client):
    assert client.get("/api/v1/brothers/state").status_code in (401, 403)
    assert client.post("/api/v1/brothers/sessions").status_code in (401, 403)


async def test_session_route_never_leaks_the_answer(client, db, learner_user):
    token = _token_for(learner_user, "learner")
    resp = client.post("/api/v1/brothers/sessions", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    body = resp.json()
    assert len(body["questions"]) == 10
    for q in body["questions"]:
        assert set(q.keys()) == {"index", "tier_id", "number", "active_digits"}
        assert "correct_answer" not in q


async def test_state_route_reports_tier_map(client, db, learner_user):
    token = _token_for(learner_user, "learner")
    resp = client.get("/api/v1/brothers/state", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 6
    assert body[0]["tier_id"] == "B1"
    assert body[0]["status"] == "active"
