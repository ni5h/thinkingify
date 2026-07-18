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
        ("self_publish", ContentStatus.draft),
        ("self_republish", ContentStatus.archived),
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
        ("self_publish", ContentStatus.published),
        ("self_republish", ContentStatus.draft),
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


async def test_self_publish_sets_published_at_and_topic_style_round_trip(db, learner_user):
    topic_id = uuid.uuid4()
    post = await content_service.create(
        db,
        learner_user,
        ContentCreate(title="My Take", content_markdown="body", topic_id=topic_id, style="documentary"),
    )
    assert post.topic_id == topic_id
    assert post.style == "documentary"

    published = await content_service.transition(db, post, "self_publish")
    assert published.status == ContentStatus.published
    assert published.published_at is not None


def _token_for(user, role: str) -> str:
    from app.core.security import create_access_token

    return create_access_token(str(user.id), email=user.email, name=user.name, role=role)


def test_self_publish_endpoint_rejects_author_role(client, author_user):
    token = _token_for(author_user, "author")
    create_resp = client.post(
        "/api/v1/content", json={"title": "Draft", "content_markdown": ""}, headers={"Authorization": f"Bearer {token}"}
    )
    content_id = create_resp.json()["id"]

    response = client.post(f"/api/v1/content/{content_id}/self-publish", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_self_publish_endpoint_accepts_learner_role_on_own_post(client, learner_user):
    token = _token_for(learner_user, "learner")
    create_resp = client.post(
        "/api/v1/content", json={"title": "My Draft", "content_markdown": ""}, headers={"Authorization": f"Bearer {token}"}
    )
    content_id = create_resp.json()["id"]

    response = client.post(f"/api/v1/content/{content_id}/self-publish", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["status"] == "published"


async def test_self_publish_endpoint_rejects_non_owner_learner(client, db, learner_user):
    owner_token = _token_for(learner_user, "learner")
    create_resp = client.post(
        "/api/v1/content",
        json={"title": "Owner's Draft", "content_markdown": ""},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    content_id = create_resp.json()["id"]

    other = User(
        id=uuid.uuid4(),
        google_sub="other-learner",
        email="other-learner@example.com",
        name="Other",
        role=UserRole.learner,
    )
    db.add(other)
    await db.commit()
    other_token = _token_for(other, "learner")

    response = client.post(f"/api/v1/content/{content_id}/self-publish", headers={"Authorization": f"Bearer {other_token}"})
    assert response.status_code == 403


def test_publish_endpoint_still_admin_only(client, learner_user):
    token = _token_for(learner_user, "learner")
    create_resp = client.post(
        "/api/v1/content", json={"title": "Draft", "content_markdown": ""}, headers={"Authorization": f"Bearer {token}"}
    )
    content_id = create_resp.json()["id"]

    response = client.post(f"/api/v1/content/{content_id}/publish", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
