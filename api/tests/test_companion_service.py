import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.schemas.content import ContentCreate
from app.schemas.topic import TopicCreate
from app.services import companion_service, content_service, topic_service
from app.services.anthropic_client import AnthropicClientError

_EXPLAINER = "Owls can rotate their heads because they have extra vertebrae in their necks."


async def _make_topic(db, admin, explainer: str = _EXPLAINER):
    return await topic_service.create(
        db,
        admin,
        TopicCreate(title="Owls", explainer_markdown=explainer, audio_url="https://cdn.test/a.mp3", themes=["animals"]),
    )


async def _make_content(db, author, topic_id=None, style="fairy_tale"):
    return await content_service.create(
        db, author, ContentCreate(title="My Owl Story", content_markdown="", topic_id=topic_id, style=style)
    )


def _mock_reply(reply: str, ladder_level: int = 1, direct_answer_requested: bool = False):
    return AsyncMock(return_value={"reply": reply, "ladder_level": ladder_level, "direct_answer_requested": direct_answer_requested})


async def test_send_message_requires_topic_linked_content(db, learner_user):
    content = await _make_content(db, learner_user, topic_id=None)
    with pytest.raises(HTTPException) as exc_info:
        await companion_service.send_message(db, learner_user, content, uuid.uuid4(), "hello")
    assert exc_info.value.status_code == 400


async def test_send_message_happy_path_persists_both_messages(db, admin_user, learner_user):
    topic = await _make_topic(db, admin_user)
    content = await _make_content(db, learner_user, topic_id=topic.id)
    session_id = uuid.uuid4()

    with patch(
        "app.services.anthropic_client.send_structured",
        _mock_reply("What part of the owl story feels most exciting to you?", ladder_level=1),
    ):
        reply = await companion_service.send_message(db, learner_user, content, session_id, "I don't know what to write")

    assert reply.role.value == "assistant"
    assert reply.ladder_level == 1
    assert reply.is_fallback is False
    assert "?" in reply.body

    history = await companion_service.list_messages(db, content)
    assert len(history) == 2
    assert history[0].role.value == "user"
    assert history[0].body == "I don't know what to write"
    assert history[1].id == reply.id


async def test_ladder_level_cannot_jump_more_than_one_rung(db, admin_user, learner_user):
    topic = await _make_topic(db, admin_user)
    content = await _make_content(db, learner_user, topic_id=topic.id)
    session_id = uuid.uuid4()

    with patch("app.services.anthropic_client.send_structured", _mock_reply("Still stuck?", ladder_level=4)):
        first = await companion_service.send_message(db, learner_user, content, session_id, "help")
    assert first.ladder_level == 2  # current (1) + 1, not the requested 4

    with patch("app.services.anthropic_client.send_structured", _mock_reply("Still stuck?", ladder_level=4)):
        second = await companion_service.send_message(db, learner_user, content, session_id, "still stuck")
    assert second.ladder_level == 3  # current (2) + 1


async def test_ladder_level_can_deescalate_freely(db, admin_user, learner_user):
    topic = await _make_topic(db, admin_user)
    content = await _make_content(db, learner_user, topic_id=topic.id)
    session_id = uuid.uuid4()

    with patch("app.services.anthropic_client.send_structured", _mock_reply("Hmm?", ladder_level=3)):
        await companion_service.send_message(db, learner_user, content, session_id, "help")
    with patch("app.services.anthropic_client.send_structured", _mock_reply("New question?", ladder_level=1)):
        second = await companion_service.send_message(db, learner_user, content, session_id, "actually a new question")
    assert second.ladder_level == 1


async def test_fact_leak_backstop_replaces_reply(db, admin_user, learner_user):
    topic = await _make_topic(db, admin_user)
    content = await _make_content(db, learner_user, topic_id=topic.id)
    session_id = uuid.uuid4()

    leaking_reply = "Well, owls have extra vertebrae in their necks, that's the secret!"
    with patch("app.services.anthropic_client.send_structured", _mock_reply(leaking_reply)):
        reply = await companion_service.send_message(db, learner_user, content, session_id, "why can owls do that")

    assert reply.fact_leak_blocked is True
    assert "vertebrae" not in reply.body


async def test_missing_nudge_gets_repaired(db, admin_user, learner_user):
    topic = await _make_topic(db, admin_user)
    content = await _make_content(db, learner_user, topic_id=topic.id)
    session_id = uuid.uuid4()

    with patch("app.services.anthropic_client.send_structured", _mock_reply("That sounds like a fun start.")):
        reply = await companion_service.send_message(db, learner_user, content, session_id, "here's my idea")

    assert reply.body.strip().endswith("?")


async def test_api_failure_returns_graceful_fallback_without_losing_ladder(db, admin_user, learner_user):
    topic = await _make_topic(db, admin_user)
    content = await _make_content(db, learner_user, topic_id=topic.id)
    session_id = uuid.uuid4()

    with patch("app.services.anthropic_client.send_structured", _mock_reply("Level two.", ladder_level=2)):
        first = await companion_service.send_message(db, learner_user, content, session_id, "help")
    assert first.ladder_level == 2

    with patch("app.services.anthropic_client.send_structured", AsyncMock(side_effect=AnthropicClientError("boom"))):
        second = await companion_service.send_message(db, learner_user, content, session_id, "again")

    assert second.is_fallback is True
    assert second.ladder_level == 2  # unchanged, not reset


async def test_direct_answer_requested_tracked_from_model_output(db, admin_user, learner_user):
    topic = await _make_topic(db, admin_user)
    content = await _make_content(db, learner_user, topic_id=topic.id)
    session_id = uuid.uuid4()

    with patch(
        "app.services.anthropic_client.send_structured",
        _mock_reply("What do you think happens next?", direct_answer_requested=True),
    ):
        reply = await companion_service.send_message(db, learner_user, content, session_id, "just tell me")

    assert reply.direct_answer_requested is True


async def test_session_message_cap_stops_calling_the_model(db, admin_user, learner_user):
    topic = await _make_topic(db, admin_user)
    content = await _make_content(db, learner_user, topic_id=topic.id)
    session_id = uuid.uuid4()

    never_call = AsyncMock(side_effect=AssertionError("should not call the model once capped"))
    with patch("app.services.anthropic_client.send_structured", _mock_reply("ok")):
        for _ in range(21):
            await companion_service.send_message(db, learner_user, content, session_id, "hi")

    with patch("app.services.anthropic_client.send_structured", never_call):
        capped = await companion_service.send_message(db, learner_user, content, session_id, "one more")

    assert capped.is_fallback is True


def _token_for(user, role: str) -> str:
    from app.core.security import create_access_token

    return create_access_token(str(user.id), email=user.email, name=user.name, role=role)


def test_companion_messages_route_requires_auth(client):
    response = client.get(f"/api/v1/content/{uuid.uuid4()}/companion/messages")
    assert response.status_code in (401, 403)


async def test_send_companion_message_route_happy_path(client, db, admin_user, learner_user):
    topic = await _make_topic(db, admin_user)
    content = await _make_content(db, learner_user, topic_id=topic.id)
    token = _token_for(learner_user, "learner")

    with patch("app.services.anthropic_client.send_structured", _mock_reply("What happens next?")):
        response = client.post(
            f"/api/v1/content/{content.id}/companion/messages",
            json={"body": "hello there", "session_id": str(uuid.uuid4())},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 201
    assert response.json()["role"] == "assistant"

    history_response = client.get(
        f"/api/v1/content/{content.id}/companion/messages", headers={"Authorization": f"Bearer {token}"}
    )
    assert history_response.status_code == 200
    assert len(history_response.json()) == 2


async def test_send_companion_message_route_rejects_non_owner(client, db, admin_user, learner_user):
    topic = await _make_topic(db, admin_user)
    content = await _make_content(db, learner_user, topic_id=topic.id)
    other_token = _token_for(admin_user, "admin")

    response = client.post(
        f"/api/v1/content/{content.id}/companion/messages",
        json={"body": "hi", "session_id": str(uuid.uuid4())},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert response.status_code == 403


def test_send_companion_message_route_404s_for_unknown_content(client, admin_user):
    token = _token_for(admin_user, "admin")
    response = client.post(
        f"/api/v1/content/{uuid.uuid4()}/companion/messages",
        json={"body": "hi", "session_id": str(uuid.uuid4())},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
