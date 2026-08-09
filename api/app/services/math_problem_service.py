import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from slugify import slugify
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.math_attempt import MathAttempt
from app.models.math_problem import MathAnswerKind, MathProblem, MathProblemStatus
from app.models.user import User
from app.schemas.math import MathProblemCreate, MathProblemUpdate

_TRANSITIONS: dict[str, tuple[MathProblemStatus, MathProblemStatus]] = {
    "publish": (MathProblemStatus.draft, MathProblemStatus.published),
    "unpublish": (MathProblemStatus.published, MathProblemStatus.draft),
}


async def _unique_slug(db: AsyncSession, title: str) -> str:
    base = slugify(title) or "problem"
    slug = base
    suffix = 2
    while True:
        result = await db.execute(select(MathProblem.id).where(MathProblem.slug == slug))
        if result.scalar_one_or_none() is None:
            return slug
        slug = f"{base}-{suffix}"
        suffix += 1


async def create(db: AsyncSession, author: User, data: MathProblemCreate) -> MathProblem:
    problem = MathProblem(
        id=uuid.uuid4(),
        title=data.title,
        slug=await _unique_slug(db, data.title),
        statement_markdown=data.statement_markdown,
        answer=data.answer,
        answer_kind=data.answer_kind,
        solution_markdown=data.solution_markdown,
        concept_tags=data.concept_tags,
        difficulty=data.difficulty,
        order_index=data.order_index,
        status=MathProblemStatus.draft,
        author_id=author.id,
    )
    db.add(problem)
    await db.commit()
    await db.refresh(problem)
    return problem


async def update(db: AsyncSession, problem: MathProblem, data: MathProblemUpdate) -> MathProblem:
    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(problem, field, value)
    await db.commit()
    await db.refresh(problem)
    return problem


async def transition(db: AsyncSession, problem: MathProblem, action: str) -> MathProblem:
    from_status, to_status = _TRANSITIONS[action]
    if problem.status != from_status:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot {action} from status '{problem.status.value}'.",
        )
    if action == "publish":
        # A problem with no answer can't be checked, and one with no
        # solution leaves the coach with no private context and nothing to
        # reveal after solving — both are the point of the room.
        if not problem.answer.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Add the answer before publishing — it's what the check compares against.",
            )
        if not problem.solution_markdown.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Add a worked solution before publishing — the coach needs it, and the kid sees it after solving.",
            )
    problem.status = to_status
    if action == "publish" and problem.published_at is None:
        problem.published_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(problem)
    return problem


async def delete(db: AsyncSession, problem: MathProblem) -> None:
    problem.deleted_at = datetime.now(UTC)
    await db.commit()


async def get_by_id(db: AsyncSession, problem_id: uuid.UUID) -> MathProblem | None:
    result = await db.execute(
        select(MathProblem).where(MathProblem.id == problem_id, MathProblem.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def get_published_by_slug(db: AsyncSession, slug: str) -> MathProblem | None:
    result = await db.execute(
        select(MathProblem).where(
            MathProblem.slug == slug,
            MathProblem.status == MathProblemStatus.published,
            MathProblem.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def list_published(db: AsyncSession) -> list[MathProblem]:
    result = await db.execute(
        select(MathProblem)
        .where(MathProblem.status == MathProblemStatus.published, MathProblem.deleted_at.is_(None))
        .order_by(MathProblem.order_index, MathProblem.created_at)
    )
    return list(result.scalars().all())


async def list_all(db: AsyncSession) -> list[MathProblem]:
    result = await db.execute(
        select(MathProblem)
        .where(MathProblem.deleted_at.is_(None))
        .order_by(MathProblem.order_index, MathProblem.created_at)
    )
    return list(result.scalars().all())


def assert_owner(problem: MathProblem, current_user: User) -> None:
    if problem.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the author of this problem.")


def _normalize(value: str, kind: MathAnswerKind) -> str | None:
    """Normalize an answer for comparison. Returns None if a value that's
    supposed to be an integer can't be parsed as one (so a non-numeric
    guess never accidentally matches)."""
    stripped = value.strip()
    if kind == MathAnswerKind.integer:
        cleaned = stripped.replace(",", "").replace(" ", "")
        try:
            return str(int(cleaned))
        except ValueError:
            return None
    return " ".join(stripped.casefold().split())


def check_answer(problem: MathProblem, submitted_answer: str) -> bool:
    submitted = _normalize(submitted_answer, problem.answer_kind)
    if submitted is None:
        return False
    return submitted == _normalize(problem.answer, problem.answer_kind)


async def record_attempt(db: AsyncSession, user: User, problem: MathProblem, submitted_answer: str) -> MathAttempt:
    attempt = MathAttempt(
        id=uuid.uuid4(),
        math_problem_id=problem.id,
        user_id=user.id,
        submitted_answer=submitted_answer,
        is_correct=check_answer(problem, submitted_answer),
    )
    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)
    return attempt
