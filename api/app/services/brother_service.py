import statistics
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brother import (
    BrotherAttempt,
    BrotherSession,
    BrotherSessionStatus,
    BrotherTierProgress,
    BrotherTierStatus,
)
from app.models.user import User
from app.services import brother_tiers
from app.services.brother_tiers import BROTHER_TIERS, TIERS_BY_ID

_SESSION_SIZE = 10

# Mastery thresholds (spec §3.2 / §3.1).
_BASELINE_SAMPLE = 10  # baseline = median response of the first N attempts
_MASTERY_MIN_ATTEMPTS = 15  # need at least this many before mastery can fire
_MASTERY_WINDOW = 20  # evaluated over the trailing N
_MASTERY_ACCURACY = 0.90
_MASTERY_SPEED_FRACTION = 0.60  # median must be <= this * baseline


async def get_or_create_state(db: AsyncSession, user: User) -> list[BrotherTierProgress]:
    result = await db.execute(select(BrotherTierProgress).where(BrotherTierProgress.user_id == user.id))
    existing = {p.tier_id: p for p in result.scalars().all()}

    created = False
    for tier in BROTHER_TIERS:
        if tier.id not in existing:
            row = BrotherTierProgress(
                id=uuid.uuid4(),
                user_id=user.id,
                tier_id=tier.id,
                status=BrotherTierStatus.active if tier.prerequisite is None else BrotherTierStatus.locked,
            )
            db.add(row)
            existing[tier.id] = row
            created = True
    if created:
        await db.commit()
        for row in existing.values():
            await db.refresh(row)

    # Return in tier order.
    return [existing[tier.id] for tier in BROTHER_TIERS]


def _current_active_tier_id(states: list[BrotherTierProgress]) -> str:
    """The frontier the child is working on: the highest-index tier with
    status active. (Falls back to the entry tier — should never be needed
    once state is seeded.)"""
    active = [s.tier_id for s in states if s.status == BrotherTierStatus.active]
    if not active:
        return brother_tiers.ENTRY_TIER_ID
    return max(active, key=lambda tid: brother_tiers.TIER_ORDER.index(tid))


async def start_session(db: AsyncSession, user: User) -> BrotherSession:
    states = await get_or_create_state(db, user)
    tier_id = _current_active_tier_id(states)
    tier = TIERS_BY_ID[tier_id]

    questions: list[dict] = []
    avoid: int | None = None
    for index in range(_SESSION_SIZE):
        n = brother_tiers.generate_number(tier, avoid=avoid)
        avoid = n
        questions.append(
            {
                "index": index,
                "tier_id": tier.id,
                "number": n,
                "active_digits": tier.active_digits,
                "is_retention": False,
                "is_preview": False,
            }
        )

    session = BrotherSession(id=uuid.uuid4(), user_id=user.id, questions=questions, answered_indexes=[])
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def record_answer(
    db: AsyncSession, user: User, session: BrotherSession, index: int, user_answer: int, response_ms: int
) -> tuple[bool, int, str | None, str | None]:
    question = next((q for q in session.questions if q["index"] == index), None)
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such question in this session.")
    if index in (session.answered_indexes or []):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="That question was already answered.")

    tier = TIERS_BY_ID[question["tier_id"]]
    correct_answer = brother_tiers.brother(question["number"], tier.power)
    is_correct = user_answer == correct_answer

    db.add(
        BrotherAttempt(
            id=uuid.uuid4(),
            user_id=user.id,
            tier_id=tier.id,
            number=question["number"],
            correct_answer=correct_answer,
            user_answer=user_answer,
            correct=is_correct,
            response_ms=response_ms,
            is_retention=question.get("is_retention", False),
            is_preview=question.get("is_preview", False),
        )
    )
    session.answered_indexes = [*(session.answered_indexes or []), index]
    if len(session.answered_indexes) >= len(session.questions):
        session.status = BrotherSessionStatus.complete
    await db.commit()

    # Preview questions never touch mastery (spec §4.1).
    mastered_tier_id: str | None = None
    unlocked_tier_id: str | None = None
    if not question.get("is_preview", False):
        mastered_tier_id, unlocked_tier_id = await _evaluate(db, user, tier.id)

    return is_correct, correct_answer, mastered_tier_id, unlocked_tier_id


async def tier_attempts(db: AsyncSession, user_id: uuid.UUID, tier_id: str) -> list[BrotherAttempt]:
    """All non-preview attempts at a tier, oldest first."""
    result = await db.execute(
        select(BrotherAttempt)
        .where(
            BrotherAttempt.user_id == user_id,
            BrotherAttempt.tier_id == tier_id,
            BrotherAttempt.is_preview.is_(False),
        )
        .order_by(BrotherAttempt.created_at)
    )
    return list(result.scalars().all())


def median_ms(attempts: list[BrotherAttempt]) -> int | None:
    if not attempts:
        return None
    return int(statistics.median(a.response_ms for a in attempts))


def accuracy(attempts: list[BrotherAttempt]) -> float | None:
    if not attempts:
        return None
    return sum(1 for a in attempts if a.correct) / len(attempts)


async def _get_progress(db: AsyncSession, user_id: uuid.UUID, tier_id: str) -> BrotherTierProgress:
    result = await db.execute(
        select(BrotherTierProgress).where(
            BrotherTierProgress.user_id == user_id, BrotherTierProgress.tier_id == tier_id
        )
    )
    return result.scalar_one()


async def _evaluate(db: AsyncSession, user: User, tier_id: str) -> tuple[str | None, str | None]:
    """The mastery brain. Sets the personal baseline once, and flips a tier
    active→mastered (unlocking the next) when accuracy AND speed both clear
    the bar over the same trailing window. Returns (mastered_tier_id,
    unlocked_tier_id) for anything that changed this call."""
    progress = await _get_progress(db, user.id, tier_id)
    if progress.status != BrotherTierStatus.active:
        return None, None

    attempts = await tier_attempts(db, user.id, tier_id)

    if progress.baseline_ms is None and len(attempts) >= _BASELINE_SAMPLE:
        progress.baseline_ms = median_ms(attempts[:_BASELINE_SAMPLE])

    if progress.baseline_ms is None or len(attempts) < _MASTERY_MIN_ATTEMPTS:
        await db.commit()
        return None, None

    window = attempts[-_MASTERY_WINDOW:]
    if accuracy(window) >= _MASTERY_ACCURACY and median_ms(window) <= _MASTERY_SPEED_FRACTION * progress.baseline_ms:
        progress.status = BrotherTierStatus.mastered
        progress.mastered_at = datetime.now(UTC)
        unlocked = await _maybe_unlock_next(db, user.id, tier_id)
        await db.commit()
        return tier_id, unlocked

    await db.commit()
    return None, None


async def _maybe_unlock_next(db: AsyncSession, user_id: uuid.UUID, mastered_tier_id: str) -> str | None:
    """One-way gate: flip the next tier locked→active now that its
    prerequisite is mastered. Never re-locks (a future demotion of an
    earlier tier must not re-lock tiers already unlocked, spec §3.4)."""
    next_id = brother_tiers.next_tier_id(mastered_tier_id)
    if next_id is None:
        return None
    next_progress = await _get_progress(db, user_id, next_id)
    if next_progress.status == BrotherTierStatus.locked:
        next_progress.status = BrotherTierStatus.active
        return next_id
    return None


async def get_session(db: AsyncSession, session_id: uuid.UUID) -> BrotherSession | None:
    result = await db.execute(select(BrotherSession).where(BrotherSession.id == session_id))
    return result.scalar_one_or_none()
