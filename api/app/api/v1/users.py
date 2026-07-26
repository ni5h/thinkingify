import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserLinkedProfileOut
from app.services import family_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}/profile", response_model=UserLinkedProfileOut)
async def get_linked_profile(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    target = await family_service.assert_linked(db, current_user, user_id)
    return target
