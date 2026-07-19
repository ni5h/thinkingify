from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException

from app.models.puzzle import PuzzleTier
from app.schemas.puzzle import AttemptCreate
from app.services import puzzle_service

GAME_ID = "kakooma"


def _attempt(time_taken_ms: int, correct: bool = True) -> AttemptCreate:
    started = datetime.now(UTC)
    return AttemptCreate(
        started_at=started,
        completed_at=started + timedelta(milliseconds=time_taken_ms),
        time_taken_ms=time_taken_ms,
        correct=correct,
    )


async def test_progress_created_with_defaults_on_first_access(db, learner_user):
    progress = await puzzle_service.get_or_create_progress(db, learner_user, GAME_ID)
    assert progress.current_tier == PuzzleTier.trial
    assert progress.variations_completed == 0
    assert progress.highest_tier_unlocked == PuzzleTier.trial


async def test_progress_reused_on_repeat_access(db, learner_user):
    first = await puzzle_service.get_or_create_progress(db, learner_user, GAME_ID)
    second = await puzzle_service.get_or_create_progress(db, learner_user, GAME_ID)
    assert first.id == second.id


async def test_unknown_game_id_raises_404(db, learner_user):
    with pytest.raises(HTTPException) as exc_info:
        await puzzle_service.get_or_create_progress(db, learner_user, "not-a-real-game")
    assert exc_info.value.status_code == 404


async def test_slow_correct_attempt_does_not_increment_variations(db, learner_user):
    # Trial target is 20_000ms — well over that, even though correct.
    _, progress, tier_advanced = await puzzle_service.record_attempt(
        db, learner_user, GAME_ID, _attempt(time_taken_ms=99_000, correct=True)
    )
    assert progress.variations_completed == 0
    assert tier_advanced is False


async def test_incorrect_fast_attempt_does_not_increment_variations(db, learner_user):
    _, progress, tier_advanced = await puzzle_service.record_attempt(
        db, learner_user, GAME_ID, _attempt(time_taken_ms=1_000, correct=False)
    )
    assert progress.variations_completed == 0
    assert tier_advanced is False


async def test_fast_correct_attempt_increments_variations(db, learner_user):
    attempt, progress, tier_advanced = await puzzle_service.record_attempt(
        db, learner_user, GAME_ID, _attempt(time_taken_ms=5_000, correct=True)
    )
    assert attempt.beat_time_limit is True
    assert attempt.variation_index == 0
    assert progress.variations_completed == 1
    assert tier_advanced is False


async def test_tier_advances_after_ten_beaten_attempts(db, learner_user):
    progress = None
    tier_advanced = False
    for _ in range(10):
        _, progress, tier_advanced = await puzzle_service.record_attempt(
            db, learner_user, GAME_ID, _attempt(time_taken_ms=5_000, correct=True)
        )
    assert tier_advanced is True
    assert progress.current_tier == PuzzleTier.beginner
    assert progress.variations_completed == 0
    assert progress.highest_tier_unlocked == PuzzleTier.beginner


async def test_failed_attempt_does_not_reset_progress_within_tier(db, learner_user):
    for _ in range(3):
        await puzzle_service.record_attempt(
            db, learner_user, GAME_ID, _attempt(time_taken_ms=5_000, correct=True)
        )
    # A slow/failed attempt in between — should not undo the 3 already banked.
    await puzzle_service.record_attempt(
        db, learner_user, GAME_ID, _attempt(time_taken_ms=99_000, correct=True)
    )
    _, progress, _ = await puzzle_service.record_attempt(
        db, learner_user, GAME_ID, _attempt(time_taken_ms=5_000, correct=True)
    )
    assert progress.variations_completed == 4


async def test_pro_tier_freezes_at_ten_no_further_advancement(db, learner_user):
    # 10 attempts per tier transition (trial->beginner->intermediate->advanced->pro
    # = 4 transitions = 40 attempts), then 10 more to fill Pro itself to 10/10.
    progress = None
    for _ in range(50):
        _, progress, _ = await puzzle_service.record_attempt(
            db, learner_user, GAME_ID, _attempt(time_taken_ms=5_000, correct=True)
        )
    assert progress.current_tier == PuzzleTier.pro
    assert progress.variations_completed == 10

    # One more beaten attempt at Pro should not overflow or wrap.
    _, progress, tier_advanced = await puzzle_service.record_attempt(
        db, learner_user, GAME_ID, _attempt(time_taken_ms=5_000, correct=True)
    )
    assert progress.current_tier == PuzzleTier.pro
    assert progress.variations_completed == 10
    assert tier_advanced is False


async def test_attempts_recorded_regardless_of_outcome(db, learner_user):
    await puzzle_service.record_attempt(db, learner_user, GAME_ID, _attempt(time_taken_ms=99_000, correct=False))
    await puzzle_service.record_attempt(db, learner_user, GAME_ID, _attempt(time_taken_ms=5_000, correct=True))

    from sqlalchemy import select

    from app.models.puzzle import PuzzleAttempt

    result = await db.execute(select(PuzzleAttempt).where(PuzzleAttempt.user_id == learner_user.id))
    attempts = result.scalars().all()
    assert len(attempts) == 2


def test_puzzle_endpoints_work_for_any_authenticated_user(client, author_user):
    """No more role gate — puzzles just require authentication."""
    from app.core.security import create_access_token

    token = create_access_token(str(author_user.id), email=author_user.email, name=author_user.name, role="author")
    response = client.get(f"/api/v1/puzzles/{GAME_ID}/progress", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["current_tier"] == "trial"


def test_puzzle_endpoints_reject_unauthenticated(client):
    response = client.get(f"/api/v1/puzzles/{GAME_ID}/progress")
    assert response.status_code in (401, 403)
