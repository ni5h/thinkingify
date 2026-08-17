from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.content import ContentListItem, ContentOut
from app.services import diary_service

router = APIRouter(prefix="/diary", tags=["diary"])


class DiaryTodayRequest(BaseModel):
    # The kid's local calendar date, so "today" matches their wall clock.
    entry_date: date


@router.post("/today", response_model=ContentOut)
async def get_or_create_today(
    body: DiaryTodayRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await diary_service.get_or_create_today(db, current_user, body.entry_date)


@router.get("/entries", response_model=list[ContentListItem])
async def list_entries(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await diary_service.list_entries(db, current_user)
