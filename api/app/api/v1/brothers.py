import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.brother import (
    BrotherAnswerCreate,
    BrotherAnswerResultOut,
    BrotherQuestionOut,
    BrotherSessionOut,
    BrotherTierStateOut,
)
from app.services import brother_service
from app.services.brother_tiers import TIERS_BY_ID

router = APIRouter(prefix="/brothers", tags=["brothers"])


@router.get("/state", response_model=list[BrotherTierStateOut])
async def get_state(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    states = await brother_service.get_or_create_state(db, current_user)
    out: list[BrotherTierStateOut] = []
    for progress in states:
        attempts = await brother_service.tier_attempts(db, current_user.id, progress.tier_id)
        out.append(
            BrotherTierStateOut(
                tier_id=progress.tier_id,
                name=TIERS_BY_ID[progress.tier_id].name,
                status=progress.status,
                baseline_ms=progress.baseline_ms,
                median_ms=brother_service.median_ms(attempts),
                accuracy=brother_service.accuracy(attempts),
                attempts_count=len(attempts),
            )
        )
    return out


@router.post("/sessions", response_model=BrotherSessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    session = await brother_service.start_session(db, current_user)
    # Deliberately map to BrotherQuestionOut so the correct answer / the
    # is_retention/is_preview internals never reach the client.
    return BrotherSessionOut(
        id=session.id,
        questions=[BrotherQuestionOut(**{k: q[k] for k in ("index", "tier_id", "number", "active_digits")}) for q in session.questions],
    )


@router.post("/sessions/{session_id}/answers", response_model=BrotherAnswerResultOut)
async def submit_answer(
    session_id: uuid.UUID,
    body: BrotherAnswerCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    session = await brother_service.get_session(db, session_id)
    if session is None or session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    correct, correct_answer, mastered_tier_id, unlocked_tier_id = await brother_service.record_answer(
        db, current_user, session, body.index, body.user_answer, body.response_ms
    )
    return BrotherAnswerResultOut(
        correct=correct,
        correct_answer=correct_answer,
        mastered_tier_id=mastered_tier_id,
        unlocked_tier_id=unlocked_tier_id,
    )
