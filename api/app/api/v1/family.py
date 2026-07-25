import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.content import ContentStatus
from app.models.family_link import FamilyLink
from app.models.user import User
from app.schemas.content import ContentListItem
from app.schemas.family import (
    ChildSummaryOut,
    FamilyLinkOut,
    FamilyLinkRequestCreate,
    FamilyLinksOut,
    UserSummary,
)
from app.services import content_service, family_service, puzzle_service

router = APIRouter(prefix="/family", tags=["family"])


async def _to_link_outs(db: AsyncSession, links: list[FamilyLink]) -> list[FamilyLinkOut]:
    if not links:
        return []
    user_ids = {uid for link in links for uid in (link.guardian_id, link.child_id)}
    users = await family_service.users_by_id(db, user_ids)
    return [
        FamilyLinkOut(
            id=link.id,
            status=link.status,
            requested_by=link.requested_by,
            guardian=UserSummary.model_validate(users[link.guardian_id]),
            child=UserSummary.model_validate(users[link.child_id]),
            created_at=link.created_at,
            accepted_at=link.accepted_at,
        )
        for link in links
    ]


async def _to_link_out(db: AsyncSession, link: FamilyLink) -> FamilyLinkOut:
    return (await _to_link_outs(db, [link]))[0]


@router.post("/requests", response_model=FamilyLinkOut, status_code=201)
async def send_request(
    body: FamilyLinkRequestCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    link = await family_service.send_request(db, current_user, body.email, body.target_role)
    return await _to_link_out(db, link)


@router.get("/requests/incoming", response_model=list[FamilyLinkOut])
async def list_incoming(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    links = await family_service.list_incoming(db, current_user)
    return await _to_link_outs(db, links)


@router.get("/requests/outgoing", response_model=list[FamilyLinkOut])
async def list_outgoing(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    links = await family_service.list_outgoing(db, current_user)
    return await _to_link_outs(db, links)


@router.post("/requests/{link_id}/accept", response_model=FamilyLinkOut)
async def accept_request(
    link_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    link = await family_service.accept(db, link_id, current_user)
    return await _to_link_out(db, link)


@router.post("/requests/{link_id}/decline", status_code=204)
async def decline_request(
    link_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await family_service.decline(db, link_id, current_user)


@router.get("/links", response_model=FamilyLinksOut)
async def list_links(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    as_guardian, as_child = await family_service.list_my_links(db, current_user)
    return FamilyLinksOut(
        as_guardian=await _to_link_outs(db, as_guardian),
        as_child=await _to_link_outs(db, as_child),
    )


@router.delete("/links/{link_id}", status_code=204)
async def unlink(
    link_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await family_service.unlink(db, link_id, current_user)


@router.get("/children/{child_id}/summary", response_model=ChildSummaryOut)
async def child_summary(
    child_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    child = await family_service.assert_accepted_guardian_of(db, current_user, child_id)
    puzzle_stats = await puzzle_service.get_stats_for_user(db, child)
    content_counts = await content_service.count_by_status_for_author(db, child_id)
    return ChildSummaryOut(
        child_id=child.id,
        child_name=child.name,
        total_puzzle_attempts=sum(s.total_attempts for s in puzzle_stats),
        puzzle_attempts_this_week=sum(s.attempts_this_week for s in puzzle_stats),
        published_post_count=content_counts[ContentStatus.published],
    )


@router.get("/children/{child_id}/content", response_model=list[ContentListItem])
async def child_content(
    child_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await family_service.assert_accepted_guardian_of(db, current_user, child_id)
    return await content_service.list_by_author(db, child_id)
