import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.companion import CompanionMessageCreate, CompanionMessageOut
from app.schemas.content import ContentCreate, ContentListItem, ContentOut, ContentUpdate
from app.schemas.spelling import SpellingAttemptRequest, SpellingCheckRequest, SpellingFlagOut
from app.services import companion_service, content_service, family_service, spelling_service

router = APIRouter(prefix="/content", tags=["content"])


async def _get_owned_or_404(db: AsyncSession, content_id: uuid.UUID, current_user: User):
    content = await content_service.get_by_id(db, content_id)
    if content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
    content_service.assert_owner(content, current_user)
    return content


async def _get_publishable_or_404(db: AsyncSession, content_id: uuid.UUID, current_user: User):
    """Like _get_owned_or_404, but for publish/archive/republish only:
    once the author has an accepted guardian, only that guardian may call
    these — not the author themself, even though they still own it.
    Deliberately kept at the router level rather than inside
    content_service, so content_service never has to import
    family_service (same layering family.py already uses to orchestrate
    both services without either depending on the other)."""
    content = await content_service.get_by_id(db, content_id)
    if content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
    if content.author_id == current_user.id:
        if await family_service.has_any_accepted_guardian(db, content.author_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This post has a linked guardian — only your guardian can publish or unpublish it.",
            )
        return content
    if await family_service.is_accepted_guardian(db, guardian_id=current_user.id, child_id=content.author_id):
        return content
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to publish or unpublish this post.")


async def _assert_self_publish_allowed(db: AsyncSession, current_user: User) -> None:
    if await family_service.has_any_accepted_guardian(db, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You have a linked guardian — submit for review instead of publishing directly.",
        )


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
    content = await _get_publishable_or_404(db, content_id, current_user)
    return await content_service.transition(db, content, "publish")


@router.post("/{content_id}/archive", response_model=ContentOut)
async def archive(
    content_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    content = await _get_publishable_or_404(db, content_id, current_user)
    return await content_service.transition(db, content, "archive")


@router.post("/{content_id}/self-publish", response_model=ContentOut)
async def self_publish(
    content_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    content = await _get_owned_or_404(db, content_id, current_user)
    await _assert_self_publish_allowed(db, current_user)
    return await content_service.transition(db, content, "self_publish")


@router.post("/{content_id}/self-republish", response_model=ContentOut)
async def self_republish(
    content_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    content = await _get_owned_or_404(db, content_id, current_user)
    await _assert_self_publish_allowed(db, current_user)
    return await content_service.transition(db, content, "self_republish")


@router.post("/{content_id}/republish", response_model=ContentOut)
async def republish(
    content_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    content = await _get_publishable_or_404(db, content_id, current_user)
    return await content_service.transition(db, content, "republish")


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    content_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    content = await _get_owned_or_404(db, content_id, current_user)
    await content_service.delete(db, content)


# --- Writing companion chat ---


@router.get("/{content_id}/companion/messages", response_model=list[CompanionMessageOut])
async def list_companion_messages(
    content_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    content = await _get_owned_or_404(db, content_id, current_user)
    return await companion_service.list_messages(db, content)


@router.post(
    "/{content_id}/companion/messages", response_model=CompanionMessageOut, status_code=status.HTTP_201_CREATED
)
async def send_companion_message(
    content_id: uuid.UUID,
    body: CompanionMessageCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    content = await _get_owned_or_404(db, content_id, current_user)
    return await companion_service.send_message(db, current_user, content, body.session_id, body.body)


# --- Spelling check ---


async def _get_owned_flag_or_404(db: AsyncSession, content_id: uuid.UUID, flag_id: uuid.UUID, current_user: User):
    content = await _get_owned_or_404(db, content_id, current_user)
    flag = await spelling_service.get_flag(db, flag_id)
    if flag is None or flag.content_id != content.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spelling flag not found.")
    return content, flag


@router.get("/{content_id}/spelling/flags", response_model=list[SpellingFlagOut])
async def list_spelling_flags(
    content_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    content = await _get_owned_or_404(db, content_id, current_user)
    return await spelling_service.list_pending(db, content)


@router.post("/{content_id}/spelling/check", response_model=list[SpellingFlagOut])
async def check_spelling(
    content_id: uuid.UUID,
    body: SpellingCheckRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    content = await _get_owned_or_404(db, content_id, current_user)
    return await spelling_service.run_check(db, content, body.text)


@router.post("/{content_id}/spelling/flags/{flag_id}/attempt", response_model=SpellingFlagOut)
async def attempt_spelling_fix(
    content_id: uuid.UUID,
    flag_id: uuid.UUID,
    body: SpellingAttemptRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    content, flag = await _get_owned_flag_or_404(db, content_id, flag_id, current_user)
    return await spelling_service.attempt_fix(db, content, flag, body.word)


@router.post("/{content_id}/spelling/flags/{flag_id}/override", response_model=SpellingFlagOut)
async def override_spelling_flag(
    content_id: uuid.UUID,
    flag_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    _, flag = await _get_owned_flag_or_404(db, content_id, flag_id, current_user)
    return await spelling_service.override(db, flag)
