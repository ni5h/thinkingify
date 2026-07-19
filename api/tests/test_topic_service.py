import pytest
from fastapi import HTTPException

from app.models.topic import TopicStatus
from app.schemas.topic import TopicCreate, TopicUpdate
from app.services import topic_service


async def _make_topic(db, admin, title: str = "Why Seasons Happen"):
    return await topic_service.create(db, admin, TopicCreate(title=title, explainer_markdown="body"))


async def test_create_generates_slug_and_defaults_to_draft(db, admin_user):
    topic = await _make_topic(db, admin_user)
    assert topic.slug == "why-seasons-happen"
    assert topic.status == TopicStatus.draft
    assert topic.author_id == admin_user.id


async def test_slug_collision_gets_numeric_suffix(db, admin_user):
    first = await _make_topic(db, admin_user, "Same Title")
    second = await _make_topic(db, admin_user, "Same Title")
    assert first.slug == "same-title"
    assert second.slug == "same-title-2"


async def test_publish_then_unpublish(db, admin_user):
    topic = await _make_topic(db, admin_user)
    published = await topic_service.transition(db, topic, "publish")
    assert published.status == TopicStatus.published
    assert published.published_at is not None

    unpublished = await topic_service.transition(db, published, "unpublish")
    assert unpublished.status == TopicStatus.draft


async def test_illegal_transition_raises_409(db, admin_user):
    topic = await _make_topic(db, admin_user)
    with pytest.raises(HTTPException) as exc_info:
        await topic_service.transition(db, topic, "unpublish")
    assert exc_info.value.status_code == 409


async def test_update_partial_fields(db, admin_user):
    topic = await _make_topic(db, admin_user)
    updated = await topic_service.update(db, topic, TopicUpdate(order_index=5))
    assert updated.order_index == 5
    assert updated.title == "Why Seasons Happen"


async def test_list_published_ordered_by_order_index(db, admin_user):
    a = await topic_service.create(db, admin_user, TopicCreate(title="A", order_index=2))
    b = await topic_service.create(db, admin_user, TopicCreate(title="B", order_index=1))
    await topic_service.transition(db, a, "publish")
    await topic_service.transition(db, b, "publish")

    published = await topic_service.list_published(db)
    assert [t.title for t in published] == ["B", "A"]


async def test_draft_topic_excluded_from_published_list(db, admin_user):
    topic = await _make_topic(db, admin_user)
    assert not any(t.id == topic.id for t in await topic_service.list_published(db))


async def test_soft_deleted_topic_excluded_from_all_lists(db, admin_user):
    topic = await _make_topic(db, admin_user)
    await topic_service.transition(db, topic, "publish")
    await topic_service.delete(db, topic)

    assert not any(t.id == topic.id for t in await topic_service.list_published(db))
    assert not any(t.id == topic.id for t in await topic_service.list_all(db))
    assert await topic_service.get_by_id(db, topic.id) is None


async def test_assert_owner(db, admin_user, author_user):
    topic = await _make_topic(db, admin_user)

    topic_service.assert_owner(topic, admin_user)  # no raise, they're the author

    with pytest.raises(HTTPException) as exc_info:
        topic_service.assert_owner(topic, author_user)
    assert exc_info.value.status_code == 403


def _token_for(user, role: str) -> str:
    from app.core.security import create_access_token

    return create_access_token(str(user.id), email=user.email, name=user.name, role=role)


def test_any_authenticated_user_can_create_a_topic(client, author_user, learner_user):
    """No more admin-only gate — creating a topic just requires being
    signed in, same as creating a blog post."""
    for user, role in [(author_user, "author"), (learner_user, "learner")]:
        token = _token_for(user, role)
        response = client.post(
            "/api/v1/topics", json={"title": f"New Topic by {role}"}, headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 201
        assert response.json()["author_id"] == str(user.id)


def test_topic_list_endpoints_are_open_to_any_authenticated_user(client, learner_user):
    token = _token_for(learner_user, "learner")
    response = client.get("/api/v1/topics", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_topic_mutation_endpoints_reject_unauthenticated(client):
    response = client.post("/api/v1/topics", json={"title": "New Topic"})
    assert response.status_code in (401, 403)


def test_topic_owner_can_update_publish_unpublish_delete(client, admin_user):
    token = _token_for(admin_user, "admin")
    create_resp = client.post(
        "/api/v1/topics", json={"title": "Owned Topic"}, headers={"Authorization": f"Bearer {token}"}
    )
    topic_id = create_resp.json()["id"]

    update_resp = client.patch(
        f"/api/v1/topics/{topic_id}", json={"order_index": 3}, headers={"Authorization": f"Bearer {token}"}
    )
    assert update_resp.status_code == 200

    publish_resp = client.post(
        f"/api/v1/topics/{topic_id}/publish", headers={"Authorization": f"Bearer {token}"}
    )
    assert publish_resp.status_code == 200

    unpublish_resp = client.post(
        f"/api/v1/topics/{topic_id}/unpublish", headers={"Authorization": f"Bearer {token}"}
    )
    assert unpublish_resp.status_code == 200

    delete_resp = client.delete(f"/api/v1/topics/{topic_id}", headers={"Authorization": f"Bearer {token}"})
    assert delete_resp.status_code == 204


def test_non_owner_cannot_update_publish_unpublish_delete(client, admin_user, learner_user):
    owner_token = _token_for(admin_user, "admin")
    create_resp = client.post(
        "/api/v1/topics", json={"title": "Someone Else's Topic"}, headers={"Authorization": f"Bearer {owner_token}"}
    )
    topic_id = create_resp.json()["id"]

    other_token = _token_for(learner_user, "learner")
    headers = {"Authorization": f"Bearer {other_token}"}

    assert client.patch(f"/api/v1/topics/{topic_id}", json={"order_index": 1}, headers=headers).status_code == 403
    assert client.post(f"/api/v1/topics/{topic_id}/publish", headers=headers).status_code == 403
    assert client.post(f"/api/v1/topics/{topic_id}/unpublish", headers=headers).status_code == 403
    assert client.delete(f"/api/v1/topics/{topic_id}", headers=headers).status_code == 403


def test_published_topics_endpoint_is_public(client):
    response = client.get("/api/v1/topics/published")
    assert response.status_code == 200
    assert response.json() == []
