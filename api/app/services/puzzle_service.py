import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.puzzle import PuzzleAttempt, PuzzleGameProgress, PuzzleTier, TIER_ORDER, next_tier
from app.models.user import User
from app.schemas.puzzle import VARIATIONS_PER_TIER, AttemptCreate, GameStatsOut, TierStatsOut

# One small integer per tier per game — not the puzzle-generation algorithm
# itself, which stays client-side (see kakooma.engine.ts's TIERS array,
# which this must be kept in sync with). This is a deliberate, targeted
# duplication: the server independently verifies the reported time against
# its own copy of the limit rather than trusting a client-sent boolean.
TIER_TARGET_TIME_MS: dict[str, dict[PuzzleTier, int]] = {
    "kakooma-add": {
        PuzzleTier.trial: 20_000,
        PuzzleTier.beginner: 12_000,
        PuzzleTier.intermediate: 15_000,
        PuzzleTier.advanced: 25_000,
        PuzzleTier.pro: 15_000,
    },
    "kakooma-subtract": {
        PuzzleTier.trial: 20_000,
        PuzzleTier.beginner: 12_000,
        PuzzleTier.intermediate: 15_000,
        PuzzleTier.advanced: 25_000,
        PuzzleTier.pro: 15_000,
    },
    "kakooma-multiply": {
        PuzzleTier.trial: 20_000,
        PuzzleTier.beginner: 12_000,
        PuzzleTier.intermediate: 18_000,
        PuzzleTier.advanced: 28_000,
        PuzzleTier.pro: 18_000,
    },
    "kakooma-divide": {
        PuzzleTier.trial: 20_000,
        PuzzleTier.beginner: 12_000,
        PuzzleTier.intermediate: 18_000,
        PuzzleTier.advanced: 28_000,
        PuzzleTier.pro: 18_000,
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

    is_practice = data.practice_tier is not None
    if is_practice:
        if TIER_ORDER.index(data.practice_tier) >= TIER_ORDER.index(progress.current_tier):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only practice a tier you've already passed.",
            )
        tier_for_attempt = data.practice_tier
    else:
        tier_for_attempt = progress.current_tier

    target_ms = TIER_TARGET_TIME_MS[game_id][tier_for_attempt]
    beat_time_limit = data.correct and data.time_taken_ms <= target_ms

    attempt = PuzzleAttempt(
        id=uuid.uuid4(),
        user_id=user.id,
        game_id=game_id,
        tier=tier_for_attempt,
        # variation_index has no meaning for a practice attempt (there's no
        # "10 variations to complete" concept in practice mode) — just 0.
        variation_index=0 if is_practice else progress.variations_completed,
        started_at=data.started_at,
        completed_at=data.completed_at,
        time_taken_ms=data.time_taken_ms,
        correct=data.correct,
        beat_time_limit=beat_time_limit,
    )
    db.add(attempt)

    tier_advanced = False
    # Practice attempts never touch variations_completed/current_tier/
    # highest_tier_unlocked — that's the entire point of practice mode.
    if not is_practice and beat_time_limit and progress.variations_completed < VARIATIONS_PER_TIER:
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


async def get_stats_for_user(db: AsyncSession, user: User) -> list[GameStatsOut]:
    """One grouped query, reused by all 3 metric surfaces (Dashboard sums
    across games, the Sherlock room shows one row per game, a Kakooma
    variation page filters to its own game_id) — see ui/CLAUDE.md. Only
    returns rows for games the user has actually attempted; the frontend
    merges this against its own static list of known games for the
    zero-state ("not started yet") cards.
    """
    now = datetime.now(UTC)
    today_start = datetime(now.year, now.month, now.day, tzinfo=UTC)
    week_start = now - timedelta(days=7)

    result = await db.execute(
        select(
            PuzzleAttempt.game_id,
            func.count(PuzzleAttempt.id).label("total_attempts"),
            func.sum(case((PuzzleAttempt.created_at >= today_start, 1), else_=0)).label("attempts_today"),
            func.sum(case((PuzzleAttempt.created_at >= week_start, 1), else_=0)).label("attempts_this_week"),
            func.sum(PuzzleAttempt.time_taken_ms).label("total_time_ms"),
            func.max(PuzzleAttempt.created_at).label("last_attempt_at"),
        )
        .where(PuzzleAttempt.user_id == user.id)
        .group_by(PuzzleAttempt.game_id)
    )
    rows = result.all()

    progress_result = await db.execute(select(PuzzleGameProgress).where(PuzzleGameProgress.user_id == user.id))
    progress_by_game = {p.game_id: p for p in progress_result.scalars().all()}

    return [
        GameStatsOut(
            game_id=row.game_id,
            current_tier=progress_by_game[row.game_id].current_tier
            if row.game_id in progress_by_game
            else PuzzleTier.trial,
            total_attempts=row.total_attempts,
            attempts_today=row.attempts_today or 0,
            attempts_this_week=row.attempts_this_week or 0,
            total_time_ms=row.total_time_ms or 0,
            last_attempt_at=row.last_attempt_at,
        )
        for row in rows
    ]


async def get_tier_stats(db: AsyncSession, user: User, game_id: str) -> list[TierStatsOut]:
    """Powers both the per-tier timing display and the practice-tier picker
    on a Kakooma variation page — see kakooma.component.ts."""
    _known_game_or_404(game_id)

    result = await db.execute(
        select(
            PuzzleAttempt.tier,
            func.count(PuzzleAttempt.id).label("attempts"),
            func.min(case((PuzzleAttempt.correct, PuzzleAttempt.time_taken_ms), else_=None)).label(
                "fastest_time_ms"
            ),
        )
        .where(PuzzleAttempt.user_id == user.id, PuzzleAttempt.game_id == game_id)
        .group_by(PuzzleAttempt.tier)
    )
    return [
        TierStatsOut(tier=row.tier, attempts=row.attempts, fastest_time_ms=row.fastest_time_ms)
        for row in result.all()
    ]
