import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.models.spelling_flag import SpellingErrorType, SpellingFlagStatus
from app.schemas.content import ContentCreate
from app.schemas.topic import TopicCreate
from app.services import content_service, spelling_service, topic_service
from app.services.anthropic_client import AnthropicClientError


async def _make_topic(db, admin, explainer: str = "Zorblatt is a fictional planet with two moons."):
    return await topic_service.create(
        db,
        admin,
        TopicCreate(title="Space", explainer_markdown=explainer, audio_url="https://cdn.test/a.mp3", themes=["space"]),
    )


async def _make_content(db, author, topic_id=None):
    return await content_service.create(
        db, author, ContentCreate(title="My Story", content_markdown="", topic_id=topic_id, style="blank")
    )


def _mock_judgments(judgments: list[dict]):
    return AsyncMock(return_value={"judgments": judgments})


async def test_misspelling_is_flagged_with_silent_e_hint(db, learner_user):
    content = await _make_content(db, learner_user)
    flags = await spelling_service.run_check(db, content, "I was hopeing you could help me.")
    words = {f.word: f for f in flags}
    assert "hopeing" in words
    flag = words["hopeing"]
    assert flag.error_type == SpellingErrorType.misspelling
    assert flag.status == SpellingFlagStatus.pending
    assert flag.suggested_correction == "hoping"
    assert "silent" in flag.hint.lower()


async def test_clean_text_produces_no_flags(db, learner_user):
    content = await _make_content(db, learner_user)
    flags = await spelling_service.run_check(db, content, "The sun was warm and the garden was quiet.")
    assert flags == []


async def test_topic_vocabulary_is_never_flagged(db, admin_user, learner_user):
    topic = await _make_topic(db, admin_user)
    content = await _make_content(db, learner_user, topic_id=topic.id)
    flags = await spelling_service.run_check(db, content, "Zorblatt has two moons in the sky.")
    assert "zorblatt" not in {f.word for f in flags}


async def test_homophone_misuse_is_flagged_via_llm(db, learner_user):
    content = await _make_content(db, learner_user)
    with patch(
        "app.services.anthropic_client.send_structured",
        _mock_judgments([{"index": 1, "correct": False, "suggested_word": "They're", "reason": "They're means they are."}]),
    ):
        flags = await spelling_service.run_check(db, content, "Their going to the store.")
    words = {f.word: f for f in flags}
    assert "their" in words
    flag = words["their"]
    assert flag.error_type == SpellingErrorType.homophone
    assert flag.suggested_correction == "They're"


async def test_homophone_used_correctly_is_not_flagged(db, learner_user):
    content = await _make_content(db, learner_user)
    with patch(
        "app.services.anthropic_client.send_structured",
        _mock_judgments([{"index": 1, "correct": True, "suggested_word": "their", "reason": ""}]),
    ):
        flags = await spelling_service.run_check(db, content, "Their dog ran into the yard.")
    assert "their" not in {f.word for f in flags}


async def test_homophone_llm_failure_is_fail_soft(db, learner_user):
    content = await _make_content(db, learner_user)
    with patch(
        "app.services.anthropic_client.send_structured",
        AsyncMock(side_effect=AnthropicClientError("boom")),
    ):
        flags = await spelling_service.run_check(db, content, "Their going to see a speling mistake.")
    words = {f.word for f in flags}
    assert "speling" in words  # dictionary pass still works
    assert "their" not in words  # homophone pass silently skipped


async def test_attempt_fix_correct_marks_self_corrected(db, learner_user):
    content = await _make_content(db, learner_user)
    flags = await spelling_service.run_check(db, content, "I was hopeing for rain.")
    flag = flags[0]

    updated = await spelling_service.attempt_fix(db, content, flag, "hoping")
    assert updated.status == SpellingFlagStatus.self_corrected
    assert updated.resolved_at is not None


async def test_attempt_fix_wrong_increments_and_reveals_at_three(db, learner_user):
    content = await _make_content(db, learner_user)
    flags = await spelling_service.run_check(db, content, "I was hopeing for rain.")
    flag = flags[0]

    for expected_count in (1, 2, 3):
        flag = await spelling_service.attempt_fix(db, content, flag, "hopeingg")
        assert flag.attempt_count == expected_count
        assert flag.status == SpellingFlagStatus.pending

    assert flag.hint_revealed is True


async def test_override_requires_two_prior_attempts(db, learner_user):
    content = await _make_content(db, learner_user)
    flags = await spelling_service.run_check(db, content, "I was hopeing for rain.")
    flag = flags[0]

    with pytest.raises(HTTPException) as exc_info:
        await spelling_service.override(db, flag)
    assert exc_info.value.status_code == 409

    flag = await spelling_service.attempt_fix(db, content, flag, "wrong1")
    flag = await spelling_service.attempt_fix(db, content, flag, "wrong2")
    resolved = await spelling_service.override(db, flag)
    assert resolved.status == SpellingFlagStatus.kept_as_is


async def test_kept_as_is_word_is_never_reflagged(db, learner_user):
    content = await _make_content(db, learner_user)
    flags = await spelling_service.run_check(db, content, "I saw a zzyzx in the field.")
    flag = flags[0]
    flag = await spelling_service.attempt_fix(db, content, flag, "wrong1")
    flag = await spelling_service.attempt_fix(db, content, flag, "wrong2")
    await spelling_service.override(db, flag)

    flags_again = await spelling_service.run_check(db, content, "The zzyzx ran across the field again.")
    assert flags_again == []


async def test_self_corrected_word_reopens_if_misspelled_again(db, learner_user):
    content = await _make_content(db, learner_user)
    flags = await spelling_service.run_check(db, content, "I was hopeing for rain.")
    flag = flags[0]
    await spelling_service.attempt_fix(db, content, flag, "hoping")

    flags_again = await spelling_service.run_check(db, content, "I was hopeing again, badly.")
    words = {f.word: f for f in flags_again}
    assert "hopeing" in words
    assert words["hopeing"].status == SpellingFlagStatus.pending
    assert words["hopeing"].attempt_count == 0


def _token_for(user, role: str) -> str:
    from app.core.security import create_access_token

    return create_access_token(str(user.id), email=user.email, name=user.name, role=role)


async def test_check_spelling_route_happy_path(client, db, learner_user):
    content = await _make_content(db, learner_user)
    token = _token_for(learner_user, "learner")

    response = client.post(
        f"/api/v1/content/{content.id}/spelling/check",
        json={"text": "I was hopeing for rain."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["word"] == "hopeing"


async def test_check_spelling_route_rejects_non_owner(client, db, admin_user, learner_user):
    content = await _make_content(db, learner_user)
    other_token = _token_for(admin_user, "admin")

    response = client.post(
        f"/api/v1/content/{content.id}/spelling/check",
        json={"text": "hopeing"},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert response.status_code == 403


async def test_attempt_and_override_routes(client, db, learner_user):
    content = await _make_content(db, learner_user)
    token = _token_for(learner_user, "learner")
    headers = {"Authorization": f"Bearer {token}"}

    check_response = client.post(
        f"/api/v1/content/{content.id}/spelling/check",
        json={"text": "I was hopeing for rain."},
        headers=headers,
    )
    flag_id = check_response.json()[0]["id"]

    attempt_response = client.post(
        f"/api/v1/content/{content.id}/spelling/flags/{flag_id}/attempt",
        json={"word": "hoping"},
        headers=headers,
    )
    assert attempt_response.status_code == 200
    assert attempt_response.json()["status"] == "self_corrected"

    list_response = client.get(f"/api/v1/content/{content.id}/spelling/flags", headers=headers)
    assert list_response.json() == []


async def test_flag_from_another_content_404s(client, db, learner_user):
    content_a = await _make_content(db, learner_user)
    content_b = await _make_content(db, learner_user)
    token = _token_for(learner_user, "learner")
    headers = {"Authorization": f"Bearer {token}"}

    check_response = client.post(
        f"/api/v1/content/{content_a.id}/spelling/check",
        json={"text": "I was hopeing for rain."},
        headers=headers,
    )
    flag_id = check_response.json()[0]["id"]

    response = client.post(
        f"/api/v1/content/{content_b.id}/spelling/flags/{flag_id}/attempt",
        json={"word": "hoping"},
        headers=headers,
    )
    assert response.status_code == 404
