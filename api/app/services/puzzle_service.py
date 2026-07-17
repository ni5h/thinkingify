import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.puzzle import PuzzleAttempt, PuzzleGameProgress, PuzzleTier, TIER_ORDER, next_tier
from app.models.user import User
from app.schemas.puzzle import VARIATIONS_PER_TIER, AttemptCreate

# One small integer per tier per game — not the puzzle-generation algorithm
# itself, which stays client-side (see kakooma.engine.ts's TIERS array,
# which this must be kept in sync with). This is a deliberate, targeted
# duplication: the server independently verifies the reported time against
# its own copy of the limit rather than trusting a client-sent boolean.
TIER_TARGET_TIME_MS: dict[str, dict[PuzzleTier, int]] = {
    "kakooma": {
        PuzzleTier.trial: 20_000,
        PuzzleTier.beginner: 12_000,
        PuzzleTier.intermediate: 15_000,
        PuzzleTier.advanced: 25_000,
        PuzzleTier.pro: 15_000,
    },
}


def _known_game_or_404(game_id: str) -> None:
    if game_id not in TIER_TARGET_TIME_MS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown game '{game_id}'.")


async def get_or_create_progress(db: AsyncSession, user: User, game_id: str) -> PuzzleGameProgress:
    _known_game_or_404(game_id)
    result = await db.execute(
        select(PuzzleGameProgress).where(
            PuzzleGameProgress.user_id == user.id, PuzzleGameProgress.game_id == game_id
        )
    )
    progress = result.scalar_one_or_none()
    if progress is None:
        progress = PuzzleGameProgress(id=uuid.uuid4(), user_id=user.id, game_id=game_id)
        db.add(progress)
        await db.commit()
        await db.refresh(progress)
    return progress


async def record_attempt(
    db: AsyncSession, user: User, game_id: str, data: AttemptCreate
) -> tuple[PuzzleAttempt, PuzzleGameProgress, bool]:
    _known_game_or_404(game_id)
    progress = await get_or_create_progress(db, user, game_id)

    target_ms = TIER_TARGET_TIME_MS[game_id][progress.current_tier]
    beat_time_limit = data.correct and data.time_taken_ms <= target_ms

    attempt = PuzzleAttempt(
        id=uuid.uuid4(),
        user_id=user.id,
        game_id=game_id,
        tier=progress.current_tier,
        variation_index=progress.variations_completed,
        started_at=data.started_at,
        completed_at=data.completed_at,
        time_taken_ms=data.time_taken_ms,
        correct=data.correct,
        beat_time_limit=beat_time_limit,
    )
    db.add(attempt)

    tier_advanced = False
    if beat_time_limit and progress.variations_completed < VARIATIONS_PER_TIER:
        progress.variations_completed += 1
        if progress.variations_completed >= VARIATIONS_PER_TIER:
            upgraded = next_tier(progress.current_tier)
            if upgraded is not None:
                progress.current_tier = upgraded
                progress.variations_completed = 0
                if TIER_ORDER.index(upgraded) > TIER_ORDER.index(progress.highest_tier_unlocked):
                    progress.highest_tier_unlocked = upgraded
                tier_advanced = True
            # else: already Pro — variations_completed stays pinned at 10.

    await db.commit()
    await db.refresh(attempt)
    await db.refresh(progress)
    return attempt, progress, tier_advanced
