import uuid
from datetime import UTC, datetime

from app.models.brother import BrotherAttempt, BrotherTierStatus
from app.services import brother_service as bs


async def test_retention_demotes_a_mastered_tier_without_relocking_the_next(db, learner_user):
    states = await bs.get_or_create_state(db, learner_user)
    t0, t1 = states[0], states[1]

    # Force T0 mastered with T1 unlocked, as if earned earlier.
    t0.status = BrotherTierStatus.mastered
    t0.mastered_at = datetime.now(UTC)
    t1.status = BrotherTierStatus.active

    # A weak retention run on T0: 3/12 correct → below the 0.70 floor.
    for i in range(12):
        db.add(
            BrotherAttempt(
                id=uuid.uuid4(), user_id=learner_user.id, tier_id=t0.tier_id, number=10,
                correct_answer=1, user_answer=(1 if i < 3 else 0), correct=(i < 3),
                response_ms=1000, is_retention=True, is_preview=False,
            )
        )
    await db.commit()

    demoted = await bs._maybe_demote(db, learner_user, t0.tier_id)
    assert demoted == t0.tier_id

    await db.refresh(t0)
    await db.refresh(t1)
    assert t0.status == BrotherTierStatus.active  # needs another look
    assert t0.mastered_at is None
    assert t1.status == BrotherTierStatus.active  # never re-locked


async def test_a_strong_mastered_tier_is_not_demoted(db, learner_user):
    states = await bs.get_or_create_state(db, learner_user)
    t0 = states[0]
    t0.status = BrotherTierStatus.mastered
    t0.mastered_at = datetime.now(UTC)
    for _ in range(12):
        db.add(
            BrotherAttempt(
                id=uuid.uuid4(), user_id=learner_user.id, tier_id=t0.tier_id, number=10,
                correct_answer=1, user_answer=1, correct=True, response_ms=800,
                is_retention=True, is_preview=False,
            )
        )
    await db.commit()
    assert await bs._maybe_demote(db, learner_user, t0.tier_id) is None
    await db.refresh(t0)
    assert t0.status == BrotherTierStatus.mastered
