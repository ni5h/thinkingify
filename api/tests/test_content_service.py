import uuid

import pytest
from fastapi import HTTPException

from app.models.content import ContentStatus
from app.models.user import User, UserRole
from app.schemas.content import ContentCreate
from app.services import content_service


async def _make_post(db, author: User, title: str = "Hello World"):
    return await content_service.create(db, author, ContentCreate(title=title, content_markdown="body"))


async def test_create_generates_slug_and_defaults_to_draft(db, author_user):
    post = await _make_post(db, author_user)
    assert post.slug == "hello-world"
    assert post.status == ContentStatus.draft
    assert post.author_id == author_user.id


async def test_slug_collision_gets_numeric_suffix(db, author_user):
    first = await _make_post(db, author_user, "Same Title")
    second = await _make_post(db, author_user, "Same Title")
    third = await _make_post(db, author_user, "Same Title")
    assert first.slug == "same-title"
    assert second.slug == "same-title-2"
    assert third.slug == "same-title-3"


@pytest.mark.parametrize(
    "action,from_status",
    [
        ("submit_for_review", ContentStatus.draft),
        ("back_to_draft", ContentStatus.pending_review),
        ("publish", ContentStatus.pending_review),
        ("archive", ContentStatus.published),
        ("republish", ContentStatus.archived),
    ],
)
async def test_legal_transition_succeeds(db, author_user, action, from_status):
    post = await _make_post(db, author_user)
    post.status = from_status
    await db.commit()
    await db.refresh(post)

    result = await content_service.transition(db, post, action)
    assert result.status != from_status


@pytest.mark.parametrize(
    "action,illegal_from_status",
    [
        ("submit_for_review", ContentStatus.published),
        ("back_to_draft", ContentStatus.draft),
        ("publish", ContentStatus.draft),
        ("publish", ContentStatus.archived),
        ("archive", ContentStatus.draft),
        ("republish", ContentStatus.published),
    ],
)
async def test_illegal_transition_raises_409(db, author_user, action, illegal_from_status):
    post = await _make_post(db, author_user)
    post.status = illegal_from_status
    await db.commit()
    await db.refresh(post)

    with pytest.raises(HTTPException) as exc_info:
        await content_service.transition(db, post, action)
    assert exc_info.value.status_code == 409


async def test_publish_sets_published_at_once_and_is_idempotent_on_republish(db, author_user):
    post = await _make_post(db, author_user)
    post.status = ContentStatus.pending_review
    await db.commit()
    await db.refresh(post)

    published = await content_service.transition(db, post, "publish")
    first_published_at = published.published_at
    assert first_published_at is not None

    archived = await content_service.transition(db, published, "archive")
    republished = await content_service.transition(db, archived, "republish")
    assert republished.published_at == first_published_at


@pytest.mark.parametrize("deletable_status", [ContentStatus.draft, ContentStatus.archived])
async def test_delete_allowed_from_draft_or_archived(db, author_user, deletable_status):
    post = await _make_post(db, author_user)
    post.status = deletable_status
    await db.commit()
    await db.refresh(post)

    await content_service.delete(db, post)
    assert post.deleted_at is not None
    assert await content_service.get_by_id(db, post.id) is None


@pytest.mark.parametrize("non_deletable_status", [ContentStatus.pending_review, ContentStatus.published])
async def test_delete_rejected_from_pending_review_or_published(db, author_user, non_deletable_status):
    post = await _make_post(db, author_user)
    post.status = non_deletable_status
    await db.commit()
    await db.refresh(post)

    with pytest.raises(HTTPException) as exc_info:
        await content_service.delete(db, post)
    assert exc_info.value.status_code == 409


async def test_soft_deleted_post_excluded_from_published_list(db, author_user):
    post = await _make_post(db, author_user)
    post.status = ContentStatus.published
    await db.commit()
    await db.refresh(post)

    assert any(p.id == post.id for p in await content_service.list_published(db))

    post.status = ContentStatus.archived
    await db.commit()
    await content_service.delete(db, post)

    assert not any(p.id == post.id for p in await content_service.list_published(db))


async def test_author_sees_only_own_posts_admin_sees_all(db, author_user, admin_user):
    await _make_post(db, author_user, "Author Post")
    await _make_post(db, admin_user, "Admin Post")

    author_titles = {p.title for p in await content_service.list_all(db, author_user)}
    admin_titles = {p.title for p in await content_service.list_all(db, admin_user)}

    assert author_titles == {"Author Post"}
    assert admin_titles == {"Author Post", "Admin Post"}


async def test_assert_owner_or_admin(db, author_user, admin_user):
    post = await _make_post(db, author_user)

    content_service.assert_owner_or_admin(post, author_user)  # no raise
    content_service.assert_owner_or_admin(post, admin_user)  # no raise

    other_author = User(
        id=uuid.uuid4(),
        google_sub="other",
        email="other@example.com",
        name="Other",
        role=UserRole.author,
    )
    with pytest.raises(HTTPException) as exc_info:
        content_service.assert_owner_or_admin(post, other_author)
    assert exc_info.value.status_code == 403
