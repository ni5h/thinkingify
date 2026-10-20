"""The adaptive engine: placement, the staircase, server-side grading, and the
answer log. The child never receives a level or a score — the engine picks the
next item and only tells the client right/wrong plus (on a wrong try) a hint and
which card to peek at.
"""
from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.curriculum import AnswerEvent, AnswerResult, Item, PracticeSession
from app.models.user import User
from app.services import concept_mastery_service, curriculum_service as svc

_CHECK_N = 5
_CHALLENGE_N = 3
_CHALLENGE_PASS = 2  # of 3 to earn the skip


def placement(think_results: list[str]) -> int:
    """Start level (1-5) from the free think-first signals on the cards."""
    if not think_results:
        return 2
    rights = sum(1 for r in think_results if r == "right")
    frac = rights / len(think_results)
    return max(1, min(5, round(1 + frac * 4)))


def apply_result(session: PracticeSession, result: str, hint_used: bool) -> None:
    """Staircase: up after two clean rights in a row; down on a "not sure" or
    two wrongs in a row. A hint-assisted right is half credit — neutral, it
    neither climbs nor drops. A single slip never moves the level much."""
    if result == "right" and not hint_used:
        session.miss_streak = 0
        session.up_streak += 1
        if session.up_streak >= 2 and session.level < 5:
            session.level += 1
            session.up_streak = 0
    elif result == "right" and hint_used:
        session.up_streak = 0
        session.miss_streak = 0
    elif result == "unsure":
        session.up_streak = 0
        session.miss_streak = 0
        if session.level > 1:
            session.level -= 1
    else:  # wrong
        session.up_streak = 0
        session.miss_streak += 1
        if session.miss_streak >= 2 and session.level > 1:
            session.level -= 1
            session.miss_streak = 0


def _pick_next(items: list[Item], asked_ids: list[str], level: int, *, challenge: bool) -> Item | None:
    pool = [i for i in items if str(i.id) not in asked_ids]
    if not pool:
        return None
    if challenge:
        return max(pool, key=lambda i: i.difficulty)
    # closest difficulty to the target level; ties break to the easier item
    return min(pool, key=lambda i: (abs(i.difficulty - level), i.difficulty))


async def start(
    db: AsyncSession, child: User, concept_id: uuid.UUID, *, think_results: list[str], mode: str
) -> tuple[PracticeSession, Item]:
    items = await svc.list_live_items(db, concept_id)
    if not items:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No live items for this concept.")

    challenge = mode == "challenge"
    level = 5 if challenge else placement(think_results)
    total = min(_CHALLENGE_N if challenge else _CHECK_N, len(items))
    first = _pick_next(items, [], level, challenge=challenge)

    session = PracticeSession(
        id=uuid.uuid4(),
        child_id=child.id,
        concept_id=concept_id,
        mode=mode,
        level=level,
        start_level=level,
        total=total,
        asked_item_ids=[str(first.id)],
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session, first


async def get_session(db: AsyncSession, child: User, session_id: uuid.UUID) -> PracticeSession:
    session = await db.get(PracticeSession, session_id)
    if session is None or session.child_id != child.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    if session.status != "active":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Session already finished.")
    return session


def _grade(item: Item, choice: str | None, unsure: bool) -> str:
    if unsure:
        return "unsure"
    return "right" if choice is not None and choice == item.answer_key else "wrong"


async def answer(
    db: AsyncSession,
    child: User,
    session: PracticeSession,
    *,
    item_id: uuid.UUID,
    choice: str | None,
    unsure: bool,
    hint_used: bool,
    ms: int | None,
) -> dict:
    if session.asked_item_ids[-1] != str(item_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Answering the wrong item.")
    item = await svc.get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")

    result = _grade(item, choice, unsure)
    db.add(
        AnswerEvent(
            id=uuid.uuid4(),
            child_id=child.id,
            item_id=item.id,
            concept_id=session.concept_id,
            level=item.difficulty,
            result=AnswerResult(result),
            hint_used=hint_used,
            ms=ms,
        )
    )

    if session.mode == "check":
        apply_result(session, result, hint_used)
    session.answered += 1
    if result == "right":
        session.right_count += 1

    await db.flush()
    if session.mode == "check":
        await concept_mastery_service.evaluate(db, child.id, session.concept_id)

    items = await svc.list_live_items(db, session.concept_id)
    done = session.answered >= session.total
    next_item = None
    if not done:
        next_item = _pick_next(items, session.asked_item_ids, session.level, challenge=(session.mode == "challenge"))
        if next_item is None:
            done = True
        else:
            session.asked_item_ids = [*session.asked_item_ids, str(next_item.id)]
    if done:
        session.status = "done"

    await db.commit()

    out = {
        "correct": result == "right",
        "unsure": result == "unsure",
        "reveal_answer": item.answer_key,
        "hint": item.hint if result != "right" else None,
        "source_asset_id": item.source_asset_id if result != "right" else None,
        "index": session.answered,
        "total": session.total,
        "done": done,
        "next_item": next_item,
    }
    if session.mode == "challenge" and done:
        out["skip_earned"] = session.right_count >= _CHALLENGE_PASS
    return out
