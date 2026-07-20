from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.puzzle import AttemptCreate, AttemptResultOut, GameProgressOut, GameStatsOut
from app.services import puzzle_service

router = APIRouter(prefix="/puzzles", tags=["puzzles"])


@router.get("/stats", response_model=list[GameStatsOut])
async def get_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await puzzle_service.get_stats_for_user(db, current_user)


@router.get("/{game_id}/progress", response_model=GameProgressOut)
async def get_progress(
    game_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await puzzle_service.get_or_create_progress(db, current_user, game_id)


@router.post("/{game_id}/attempts", response_model=AttemptResultOut, status_code=201)
async def record_attempt(
    game_id: str,
    body: AttemptCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    attempt, progress, tier_advanced = await puzzle_service.record_attempt(db, current_user, game_id, body)
    return AttemptResultOut(attempt=attempt, progress=progress, tier_advanced=tier_advanced)
