"""Parent-facing insights into a child's Learn activity.

Strictly gated: a guardian only ever sees the data of a child they are an
accepted guardian of. Everything is framed against the child's OWN past — no
ranks, no scores, no comparison to other children (the pilot's rule).
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.curriculum import ActivityEvent, AnswerEvent, AnswerResult
from app.models.user import User
from app.services import concept_mastery_service, curriculum_service as svc, family_service
from app.services.mastery_math import credited_accuracy

_MAX_REPORT_SECONDS = 3600  # ignore a single report longer than an hour (bad data)
_WINDOW = 8


async def record_activity(
    db: AsyncSession, child: User, *, concept_id: uuid.UUID | None, context: str, seconds: int
) -> None:
    seconds = max(0, min(int(seconds), _MAX_REPORT_SECONDS))
    if seconds == 0:
        return
    db.add(
        ActivityEvent(
            id=uuid.uuid4(), child_id=child.id, concept_id=concept_id,
            context=(context or "learn")[:20], seconds=seconds,
        )
    )
    await db.commit()


async def list_children(db: AsyncSession, guardian: User) -> list[User]:
    as_guardian, _ = await family_service.list_my_links(db, guardian)
    child_ids = [link.child_id for link in as_guardian]
    if not child_ids:
        return []
    rows = await db.execute(select(User).where(User.id.in_(child_ids)))
    return list(rows.scalars().all())


async def _assert_guardian(db: AsyncSession, guardian: User, child_id: uuid.UUID) -> None:
    if not await family_service.is_accepted_guardian(db, guardian_id=guardian.id, child_id=child_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your child.")


def _working_at(events: list[AnswerEvent]) -> str | None:
    """Comfortable vs stretching, from the child's own recent answers — never a
    score. None until there's enough to say."""
    graded = [e for e in events if e.result != AnswerResult.unsure]
    if len(graded) < 3:
        return None
    window = events[-_WINDOW:]
    acc = credited_accuracy([e.result.value for e in window], [e.hint_used for e in window])
    if acc is None:
        return None
    return "comfortable" if acc >= 0.85 else "stretching"


async def child_overview(db: AsyncSession, guardian: User, child_id: uuid.UUID) -> dict:
    await _assert_guardian(db, guardian, child_id)
    child = await db.get(User, child_id)

    week_ago = datetime.now(UTC) - timedelta(days=7)
    seconds = (
        await db.execute(
            select(func.coalesce(func.sum(ActivityEvent.seconds), 0)).where(
                ActivityEvent.child_id == child_id, ActivityEvent.created_at >= week_ago
            )
        )
    ).scalar_one()

    events = (
        await db.execute(select(AnswerEvent).where(AnswerEvent.child_id == child_id).order_by(AnswerEvent.created_at))
    ).scalars().all()
    by_concept: dict[str, list[AnswerEvent]] = {}
    for e in events:
        by_concept.setdefault(str(e.concept_id), []).append(e)

    chapters_out: list[dict] = []
    title_by_id: dict[str, str] = {}
    solid = total = 0
    for subject in await svc.list_subjects(db):
        for chapter in await svc.list_chapters(db, subject.id):
            concepts = await svc.list_concepts(db, chapter.id)
            if not concepts:
                continue
            progress = {str(p["concept_id"]): p for p in await concept_mastery_service.concept_progress(db, child_id, concepts)}
            clist = []
            for c in sorted(concepts, key=lambda x: x.order_index):
                state = progress.get(str(c.id), {}).get("state", "learning")
                total += 1
                if state == "solid":
                    solid += 1
                title_by_id[str(c.id)] = c.title
                clist.append({
                    "concept_id": c.id, "title": c.title, "state": state,
                    "working_at": _working_at(by_concept.get(str(c.id), [])),
                })
            chapters_out.append({"chapter_id": chapter.id, "subject": subject.code, "title": chapter.title, "concepts": clist})

    recent: list[dict] = []
    seen: set[str] = set()
    for e in reversed(events):
        key = str(e.concept_id)
        if key in seen:
            continue
        seen.add(key)
        recent.append({"concept_title": title_by_id.get(key, "a concept"), "when": e.created_at})
        if len(recent) >= 5:
            break

    return {
        "child": {"id": child.id, "name": child.name},
        "time_this_week_minutes": round(seconds / 60),
        "solid_count": solid,
        "total_concepts": total,
        "chapters": chapters_out,
        "recent": recent,
    }


async def child_digest(db: AsyncSession, guardian: User, child_id: uuid.UUID) -> dict:
    overview = await child_overview(db, guardian, child_id)
    name = overview["child"]["name"]
    concepts = [c for ch in overview["chapters"] for c in ch["concepts"]]
    needs = [c["title"] for c in concepts if c["state"] == "needs_look"]
    stretching = [c["title"] for c in concepts if c["working_at"] == "stretching"]

    lines = [
        f"{name} has {overview['solid_count']} of {overview['total_concepts']} concepts solid, "
        f"with about {overview['time_this_week_minutes']} minutes this week."
    ]
    if needs:
        lines.append(f"Worth another look together: {needs[0]}.")
    elif stretching:
        lines.append(f"Currently stretching on: {stretching[0]} — a good sign.")
    else:
        lines.append("Nothing needs another look right now.")
    if overview["recent"]:
        lines.append(f"Talk about: “{overview['recent'][0]['concept_title']}” — ask what they found interesting.")

    return {"lines": lines}
