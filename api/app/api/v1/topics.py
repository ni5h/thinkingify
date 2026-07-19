import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.note import NoteOut, NoteUpdate
from app.schemas.topic import TopicCreate, TopicListItem, TopicOut, TopicUpdate
from app.services import note_service, topic_service

router = APIRouter(prefix="/topics", tags=["topics"])


async def _get_or_404(db: AsyncSession, topic_id: uuid.UUID):
    topic = await topic_service.get_by_id(db, topic_id)
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found.")
    return topic


async def _get_owned_or_404(db: AsyncSession, topic_id: uuid.UUID, current_user: User):
    topic = await _get_or_404(db, topic_id)
    topic_service.assert_owner(topic, current_user)
    return topic


@router.get("/published", response_model=list[TopicListItem])
async def list_published(db: Annotated[AsyncSession, Depends(get_db)]):
    return await topic_service.list_published(db)


@router.get("/published/{slug}", response_model=TopicOut)
async def get_published_by_slug(slug: str, db: Annotated[AsyncSession, Depends(get_db)]):
    topic = await topic_service.get_published_by_slug(db, slug)
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found.")
    return topic


# list_all/get_one are open to any authenticated user with no ownership
# check — shared visibility so people can see what topics already exist
# before creating a new one. Only mutation is ownership-gated (below).
@router.get("", response_model=list[TopicListItem])
async def list_all(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await topic_service.list_all(db)


@router.get("/{topic_id}", response_model=TopicOut)
async def get_one(
    topic_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await _get_or_404(db, topic_id)


@router.post("", response_model=TopicOut, status_code=status.HTTP_201_CREATED)
async def create(
    body: TopicCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await topic_service.create(db, current_user, body)


@router.patch("/{topic_id}", response_model=TopicOut)
async def update(
    topic_id: uuid.UUID,
    body: TopicUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    topic = await _get_owned_or_404(db, topic_id, current_user)
    return await topic_service.update(db, topic, body)


@router.post("/{topic_id}/publish", response_model=TopicOut)
async def publish(
    topic_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    topic = await _get_owned_or_404(db, topic_id, current_user)
    return await topic_service.transition(db, topic, "publish")


@router.post("/{topic_id}/unpublish", response_model=TopicOut)
async def unpublish(
    topic_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    topic = await _get_owned_or_404(db, topic_id, current_user)
    return await topic_service.transition(db, topic, "unpublish")


@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    topic_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    topic = await _get_owned_or_404(db, topic_id, current_user)
    await topic_service.delete(db, topic)


# --- Notes: one evolving scratchpad per topic per user ---


@router.get("/{topic_id}/notes", response_model=NoteOut)
async def get_note(
    topic_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await note_service.get_or_create(db, current_user, topic_id)


@router.patch("/{topic_id}/notes", response_model=NoteOut)
async def update_note(
    topic_id: uuid.UUID,
    body: NoteUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    note = await note_service.get_or_create(db, current_user, topic_id)
    return await note_service.update(db, note, body.body)
