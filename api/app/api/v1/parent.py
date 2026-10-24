import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.parent import ActivityIn, ChildOut, DigestOut, OverviewOut
from app.services import parent_insights_service as pins

# Learner reports its own time-on-task; a guardian reads a linked child's
# insights (gated inside the service to accepted guardians only).
router = APIRouter(tags=["parent"])

Db = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("/me/activity", status_code=status.HTTP_204_NO_CONTENT)
async def report_activity(payload: ActivityIn, db: Db, user: CurrentUser) -> None:
    await pins.record_activity(db, user, concept_id=payload.concept_id, context=payload.context, seconds=payload.seconds)


@router.get("/parent/children", response_model=list[ChildOut])
async def my_children(db: Db, user: CurrentUser):
    return await pins.list_children(db, user)


@router.get("/parent/children/{child_id}/overview", response_model=OverviewOut)
async def child_overview(child_id: uuid.UUID, db: Db, user: CurrentUser):
    return await pins.child_overview(db, user, child_id)


@router.get("/parent/children/{child_id}/digest", response_model=DigestOut)
async def child_digest(child_id: uuid.UUID, db: Db, user: CurrentUser):
    return await pins.child_digest(db, user, child_id)
