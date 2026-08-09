import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.math import (
    MathAttemptCreate,
    MathAttemptOut,
    MathCoachMessageCreate,
    MathCoachMessageOut,
    MathProblemAdminOut,
    MathProblemCreate,
    MathProblemListItem,
    MathProblemOut,
    MathProblemUpdate,
)
from app.services import math_coach_service, math_problem_service

router = APIRouter(prefix="/math", tags=["math"])


async def _get_or_404(db: AsyncSession, problem_id: uuid.UUID):
    problem = await math_problem_service.get_by_id(db, problem_id)
    if problem is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found.")
    return problem


async def _get_owned_or_404(db: AsyncSession, problem_id: uuid.UUID, current_user: User):
    problem = await _get_or_404(db, problem_id)
    math_problem_service.assert_owner(problem, current_user)
    return problem


# --- Public reads (kid path — answer + solution never exposed) ---


@router.get("/problems/published", response_model=list[MathProblemListItem])
async def list_published(db: Annotated[AsyncSession, Depends(get_db)]):
    return await math_problem_service.list_published(db)


@router.get("/problems/published/{slug}", response_model=MathProblemOut)
async def get_published_by_slug(slug: str, db: Annotated[AsyncSession, Depends(get_db)]):
    problem = await math_problem_service.get_published_by_slug(db, slug)
    if problem is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found.")
    return problem


# --- Authoring (author-gated; drives the future admin editor) ---


@router.get("/problems", response_model=list[MathProblemListItem])
async def list_all(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await math_problem_service.list_all(db)


@router.get("/problems/{problem_id}", response_model=MathProblemAdminOut)
async def get_one(
    problem_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await _get_owned_or_404(db, problem_id, current_user)


@router.post("/problems", response_model=MathProblemAdminOut, status_code=status.HTTP_201_CREATED)
async def create(
    body: MathProblemCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await math_problem_service.create(db, current_user, body)


@router.patch("/problems/{problem_id}", response_model=MathProblemAdminOut)
async def update(
    problem_id: uuid.UUID,
    body: MathProblemUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    problem = await _get_owned_or_404(db, problem_id, current_user)
    return await math_problem_service.update(db, problem, body)


@router.post("/problems/{problem_id}/publish", response_model=MathProblemAdminOut)
async def publish(
    problem_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    problem = await _get_owned_or_404(db, problem_id, current_user)
    return await math_problem_service.transition(db, problem, "publish")


@router.post("/problems/{problem_id}/unpublish", response_model=MathProblemAdminOut)
async def unpublish(
    problem_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    problem = await _get_owned_or_404(db, problem_id, current_user)
    return await math_problem_service.transition(db, problem, "unpublish")


@router.delete("/problems/{problem_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    problem_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    problem = await _get_owned_or_404(db, problem_id, current_user)
    await math_problem_service.delete(db, problem)


# --- Socratic coach chat ---


@router.get("/problems/{problem_id}/coach/messages", response_model=list[MathCoachMessageOut])
async def list_coach_messages(
    problem_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    problem = await _get_or_404(db, problem_id)
    return await math_coach_service.list_messages(db, problem)


@router.post(
    "/problems/{problem_id}/coach/messages",
    response_model=MathCoachMessageOut,
    status_code=status.HTTP_201_CREATED,
)
async def send_coach_message(
    problem_id: uuid.UUID,
    body: MathCoachMessageCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    problem = await _get_or_404(db, problem_id)
    return await math_coach_service.send_message(db, current_user, problem, body.session_id, body.body)


# --- Answer attempts (server-checked against the hidden answer) ---


@router.post("/problems/{problem_id}/attempts", response_model=MathAttemptOut)
async def submit_attempt(
    problem_id: uuid.UUID,
    body: MathAttemptCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    problem = await _get_or_404(db, problem_id)
    attempt = await math_problem_service.record_attempt(db, current_user, problem, body.submitted_answer)
    result = MathAttemptOut.model_validate(attempt)
    # The worked solution is the post-solve payoff — revealed only once the
    # kid has actually got it right, never before.
    if attempt.is_correct:
        result = result.model_copy(update={"solution_markdown": problem.solution_markdown})
    return result
