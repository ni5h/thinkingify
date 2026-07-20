from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException

from app.models.puzzle import PuzzleTier
from app.schemas.puzzle import AttemptCreate
from app.services import puzzle_service

GAME_IDS = ["kakooma-add", "kakooma-subtract", "kakooma-multiply", "kakooma-divide"]


@pytest.fixture(params=GAME_IDS)
def game_id(request) -> str:
    """Runs every test that uses this fixture once per Kakooma operation,
    confirming tier timing/advancement works identically and independently
    for each — see TIER_TARGET_TIME_MS in puzzle_service.py."""
    return request.param


def _attempt(time_taken_ms: int, correct: bool = True) -> AttemptCreate:
    started = datetime.now(UTC)
    return AttemptCreate(
        started_at=started,
        completed_at=started + timedelta(milliseconds=time_taken_ms),
        time_taken_ms=time_taken_ms,
        correct=correct,
    )


async def test_progress_created_with_defaults_on_first_access(db, learner_user, game_id):
    progress = await puzzle_service.get_or_create_progress(db, learner_user, game_id)
    assert progress.current_tier == PuzzleTier.trial
    assert progress.variations_completed == 0
    assert progress.highest_tier_unlocked == PuzzleTier.trial


async def test_progress_reused_on_repeat_access(db, learner_user, game_id):
    first = await puzzle_service.get_or_create_progress(db, learner_user, game_id)
    second = await puzzle_service.get_or_create_progress(db, learner_user, game_id)
    assert first.id == second.id


async def test_unknown_game_id_raises_404(db, learner_user):
    with pytest.raises(HTTPException) as exc_info:
        await puzzle_service.get_or_create_progress(db, learner_user, "not-a-real-game")
    assert exc_info.value.status_code == 404


async def test_slow_correct_attempt_does_not_increment_variations(db, learner_user, game_id):
    # Trial target is 20_000ms for every operation — well over that, even though correct.
    _, progress, tier_advanced = await puzzle_service.record_attempt(
        db, learner_user, game_id, _attempt(time_taken_ms=99_000, correct=True)
    )
    assert progress.variations_completed == 0
    assert tier_advanced is False


async def test_incorrect_fast_attempt_does_not_increment_variations(db, learner_user, game_id):
    _, progress, tier_advanced = await puzzle_service.record_attempt(
        db, learner_user, game_id, _attempt(time_taken_ms=1_000, correct=False)
    )
    assert progress.variations_completed == 0
    assert tier_advanced is False


async def test_fast_correct_attempt_increments_variations(db, learner_user, game_id):
    attempt, progress, tier_advanced = await puzzle_service.record_attempt(
        db, learner_user, game_id, _attempt(time_taken_ms=5_000, correct=True)
    )
    assert attempt.beat_time_limit is True
    assert attempt.variation_index == 0
    assert progress.variations_completed == 1
    assert tier_advanced is False


async def test_tier_advances_after_ten_beaten_attempts(db, learner_user, game_id):
    progress = None
    tier_advanced = False
    for _ in range(10):
        _, progress, tier_advanced = await puzzle_service.record_attempt(
            db, learner_user, game_id, _attempt(time_taken_ms=5_000, correct=True)
        )
    assert tier_advanced is True
    assert progress.current_tier == PuzzleTier.beginner
    assert progress.variations_completed == 0
    assert progress.highest_tier_unlocked == PuzzleTier.beginner


async def test_failed_attempt_does_not_reset_progress_within_tier(db, learner_user, game_id):
    for _ in range(3):
        await puzzle_service.record_attempt(
            db, learner_user, game_id, _attempt(time_taken_ms=5_000, correct=True)
        )
    # A slow/failed attempt in between — should not undo the 3 already banked.
    await puzzle_service.record_attempt(
        db, learner_user, game_id, _attempt(time_taken_ms=99_000, correct=True)
    )
    _, progress, _ = await puzzle_service.record_attempt(
        db, learner_user, game_id, _attempt(time_taken_ms=5_000, correct=True)
    )
    assert progress.variations_completed == 4


async def test_pro_tier_freezes_at_ten_no_further_advancement(db, learner_user, game_id):
    # 10 attempts per tier transition (trial->beginner->intermediate->advanced->pro
    # = 4 transitions = 40 attempts), then 10 more to fill Pro itself to 10/10.
    progress = None
    for _ in range(50):
        _, progress, _ = await puzzle_service.record_attempt(
            db, learner_user, game_id, _attempt(time_taken_ms=5_000, correct=True)
        )
    assert progress.current_tier == PuzzleTier.pro
    assert progress.variations_completed == 10

    # One more beaten attempt at Pro should not overflow or wrap.
    _, progress, tier_advanced = await puzzle_service.record_attempt(
        db, learner_user, game_id, _attempt(time_taken_ms=5_000, correct=True)
    )
    assert progress.current_tier == PuzzleTier.pro
    assert progress.variations_completed == 10
    assert tier_advanced is False


async def test_attempts_recorded_regardless_of_outcome(db, learner_user, game_id):
    await puzzle_service.record_attempt(db, learner_user, game_id, _attempt(time_taken_ms=99_000, correct=False))
    await puzzle_service.record_attempt(db, learner_user, game_id, _attempt(time_taken_ms=5_000, correct=True))

    from sqlalchemy import select

    from app.models.puzzle import PuzzleAttempt

    result = await db.execute(
        select(PuzzleAttempt).where(PuzzleAttempt.user_id == learner_user.id, PuzzleAttempt.game_id == game_id)
    )
    attempts = result.scalars().all()
    assert len(attempts) == 2


async def test_progress_is_independent_per_game_id(db, learner_user):
    """Advancing kakooma-add shouldn't affect kakooma-subtract's progress —
    each of the 4 operations tracks its own tier independently."""
    for _ in range(10):
        await puzzle_service.record_attempt(
            db, learner_user, "kakooma-add", _attempt(time_taken_ms=5_000, correct=True)
        )
    add_progress = await puzzle_service.get_or_create_progress(db, learner_user, "kakooma-add")
    subtract_progress = await puzzle_service.get_or_create_progress(db, learner_user, "kakooma-subtract")

    assert add_progress.current_tier == PuzzleTier.beginner
    assert subtract_progress.current_tier == PuzzleTier.trial


def test_puzzle_endpoints_work_for_any_authenticated_user(client, author_user):
    """No more role gate — puzzles just require authentication."""
    from app.core.security import create_access_token

    token = create_access_token(str(author_user.id), email=author_user.email, name=author_user.name, role="author")
    response = client.get("/api/v1/puzzles/kakooma-add/progress", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["current_tier"] == "trial"


def test_puzzle_endpoints_reject_unauthenticated(client):
    response = client.get("/api/v1/puzzles/kakooma-add/progress")
    assert response.status_code in (401, 403)


async def test_get_stats_for_user_empty_when_no_attempts(db, learner_user):
    stats = await puzzle_service.get_stats_for_user(db, learner_user)
    assert stats == []


async def test_get_stats_for_user_groups_by_game_id(db, learner_user):
    await puzzle_service.record_attempt(
        db, learner_user, "kakooma-add", _attempt(time_taken_ms=5_000, correct=True)
    )
    await puzzle_service.record_attempt(
        db, learner_user, "kakooma-add", _attempt(time_taken_ms=6_000, correct=False)
    )
    await puzzle_service.record_attempt(
        db, learner_user, "kakooma-divide", _attempt(time_taken_ms=7_000, correct=True)
    )

    stats = {s.game_id: s for s in await puzzle_service.get_stats_for_user(db, learner_user)}

    assert stats["kakooma-add"].total_attempts == 2
    assert stats["kakooma-add"].total_time_ms == 11_000
    assert stats["kakooma-divide"].total_attempts == 1
    assert stats["kakooma-divide"].total_time_ms == 7_000


async def test_get_stats_for_user_today_and_week_boundaries(db, learner_user):
    from sqlalchemy import select

    from app.models.puzzle import PuzzleAttempt

    await puzzle_service.record_attempt(
        db, learner_user, "kakooma-add", _attempt(time_taken_ms=5_000, correct=True)
    )

    # Backdate a second attempt to 10 days ago — outside the rolling
    # 7-day window and obviously outside "today" too.
    result = await db.execute(
        select(PuzzleAttempt).where(PuzzleAttempt.user_id == learner_user.id, PuzzleAttempt.game_id == "kakooma-add")
    )
    old_attempt = result.scalars().first()
    old_attempt.created_at = datetime.now(UTC) - timedelta(days=10)
    await db.commit()

    await puzzle_service.record_attempt(
        db, learner_user, "kakooma-add", _attempt(time_taken_ms=5_000, correct=True)
    )

    stats = (await puzzle_service.get_stats_for_user(db, learner_user))[0]
    assert stats.total_attempts == 2
    assert stats.attempts_today == 1
    assert stats.attempts_this_week == 1


async def test_get_stats_for_user_includes_current_tier(db, learner_user):
    for _ in range(10):
        await puzzle_service.record_attempt(
            db, learner_user, "kakooma-add", _attempt(time_taken_ms=5_000, correct=True)
        )
    stats = (await puzzle_service.get_stats_for_user(db, learner_user))[0]
    assert stats.current_tier == PuzzleTier.beginner


async def test_get_stats_for_user_scoped_to_requesting_user_only(db, learner_user, admin_user):
    await puzzle_service.record_attempt(
        db, learner_user, "kakooma-add", _attempt(time_taken_ms=5_000, correct=True)
    )
    await puzzle_service.record_attempt(
        db, admin_user, "kakooma-add", _attempt(time_taken_ms=5_000, correct=True)
    )

    learner_stats = (await puzzle_service.get_stats_for_user(db, learner_user))[0]
    assert learner_stats.total_attempts == 1


def test_stats_endpoint_requires_authentication(client):
    response = client.get("/api/v1/puzzles/stats")
    assert response.status_code in (401, 403)


def test_stats_endpoint_returns_own_stats(client, learner_user):
    from app.core.security import create_access_token

    token = create_access_token(str(learner_user.id), email=learner_user.email, name=learner_user.name, role="learner")
    create_resp = client.post(
        "/api/v1/puzzles/kakooma-add/attempts",
        json={
            "started_at": datetime.now(UTC).isoformat(),
            "completed_at": datetime.now(UTC).isoformat(),
            "time_taken_ms": 5000,
            "correct": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_resp.status_code == 201

    response = client.get("/api/v1/puzzles/stats", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["game_id"] == "kakooma-add"
    assert body[0]["total_attempts"] == 1
