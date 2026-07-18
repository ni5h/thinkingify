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


def _token_for(user, role: str) -> str:
    from app.core.security import create_access_token

    return create_access_token(str(user.id), email=user.email, name=user.name, role=role)


def test_topic_mutation_endpoints_reject_non_admin(client, author_user):
    token = _token_for(author_user, "author")
    response = client.post(
        "/api/v1/topics", json={"title": "New Topic"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_topic_mutation_endpoints_reject_learner(client, learner_user):
    token = _token_for(learner_user, "learner")
    response = client.post(
        "/api/v1/topics", json={"title": "New Topic"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_topic_mutation_endpoints_accept_admin(client, admin_user):
    token = _token_for(admin_user, "admin")
    response = client.post(
        "/api/v1/topics", json={"title": "New Topic"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201


def test_published_topics_endpoint_is_public(client):
    response = client.get("/api/v1/topics/published")
    assert response.status_code == 200
    assert response.json() == []
