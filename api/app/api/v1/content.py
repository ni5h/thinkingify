import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.content import ContentCreate, ContentListItem, ContentOut, ContentUpdate
from app.services import content_service

router = APIRouter(prefix="/content", tags=["content"])


async def _get_owned_or_404(db: AsyncSession, content_id: uuid.UUID, current_user: User):
    content = await content_service.get_by_id(db, content_id)
    if content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
    content_service.assert_owner(content, current_user)
    return content


@router.get("/published", response_model=list[ContentListItem])
async def list_published(db: Annotated[AsyncSession, Depends(get_db)]):
    return await content_service.list_published(db)


@router.get("/published/{slug}", response_model=ContentOut)
async def get_published_by_slug(slug: str, db: Annotated[AsyncSession, Depends(get_db)]):
    content = await content_service.get_published_by_slug(db, slug)
    if content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
    return content


@router.get("", response_model=list[ContentListItem])
async def list_all(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await content_service.list_all(db, current_user)


@router.get("/{content_id}", response_model=ContentOut)
async def get_one(
    content_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await _get_owned_or_404(db, content_id, current_user)


@router.post("", response_model=ContentOut, status_code=status.HTTP_201_CREATED)
async def create(
    body: ContentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await content_service.create(db, current_user, body)


@router.patch("/{content_id}", response_model=ContentOut)
async def update(
    content_id: uuid.UUID,
    body: ContentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    content = await _get_owned_or_404(db, content_id, current_user)
    return await content_service.update(db, content, body)


@router.post("/{content_id}/submit-for-review", response_model=ContentOut)
async def submit_for_review(
    content_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    content = await _get_owned_or_404(db, content_id, current_user)
    return await content_service.transition(db, content, "submit_for_review")


@router.post("/{content_id}/back-to-draft", response_model=ContentOut)
async def back_to_draft(
    content_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    content = await _get_owned_or_404(db, content_id, current_user)
    return await content_service.transition(db, content, "back_to_draft")


@router.post("/{content_id}/publish", response_model=ContentOut)
async def publish(
    content_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    content = await _get_owned_or_404(db, content_id, current_user)
    return await content_service.transition(db, content, "publish")


@router.post("/{content_id}/archive", response_model=ContentOut)
async def archive(
    content_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    content = await _get_owned_or_404(db, content_id, current_user)
    return await content_service.transition(db, content, "archive")


@router.post("/{content_id}/self-publish", response_model=ContentOut)
async def self_publish(
    content_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    content = await _get_owned_or_404(db, content_id, current_user)
    return await content_service.transition(db, content, "self_publish")


@router.post("/{content_id}/self-republish", response_model=ContentOut)
async def self_republish(
    content_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    content = await _get_owned_or_404(db, content_id, current_user)
    return await content_service.transition(db, content, "self_republish")


@router.post("/{content_id}/republish", response_model=ContentOut)
async def republish(
    content_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    content = await _get_owned_or_404(db, content_id, current_user)
    return await content_service.transition(db, content, "republish")


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    content_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    content = await _get_owned_or_404(db, content_id, current_user)
    await content_service.delete(db, content)
