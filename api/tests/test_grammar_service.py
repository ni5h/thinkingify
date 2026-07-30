from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.models.grammar_flag import GrammarFlagStatus
from app.schemas.content import ContentCreate
from app.services import content_service, grammar_service
from app.services.anthropic_client import AnthropicClientError


async def _make_content(db, author, style="blank"):
    return await content_service.create(
        db, author, ContentCreate(title="My Story", content_markdown="", style=style)
    )


def _mock_judgments(judgments: list[dict]):
    return AsyncMock(return_value={"judgments": judgments})


async def test_clean_text_produces_no_flags(db, learner_user):
    content = await _make_content(db, learner_user)
    with patch(
        "app.services.anthropic_client.send_structured",
        _mock_judgments([{"index": 1, "violates": False, "concept_id": ""}]),
    ):
        flags = await grammar_service.run_check(db, content, "The dogs run across the yard.")
    assert flags == []


async def test_subject_verb_agreement_is_flagged(db, learner_user):
    content = await _make_content(db, learner_user)
    with patch(
        "app.services.anthropic_client.send_structured",
        _mock_judgments([{"index": 1, "violates": True, "concept_id": "subject_verb_agreement"}]),
    ):
        flags = await grammar_service.run_check(db, content, "The dogs runs across the yard.")
    assert len(flags) == 1
    assert flags[0].concept_id == "subject_verb_agreement"
    assert flags[0].sentence == "The dogs runs across the yard."
    assert flags[0].status == GrammarFlagStatus.pending

    out = grammar_service.to_out(flags[0])
    assert out.concept_label == "Subject and verb agreement"
    assert len(out.example_pairs) == 2


async def test_diary_entry_style_never_flags_tense_consistency(db, learner_user):
    content = await _make_content(db, learner_user, style="diary_entry")
    # Even if the model hallucinates a tense_consistency judgment anyway,
    # it's not in the active concept set for diary_entry — filtered
    # deterministically in code, not just prompted against.
    with patch(
        "app.services.anthropic_client.send_structured",
        _mock_judgments([{"index": 1, "violates": True, "concept_id": "tense_consistency"}]),
    ):
        flags = await grammar_service.run_check(db, content, "She walked to the store and buys some milk.")
    assert flags == []


async def test_llm_failure_is_fail_soft(db, learner_user):
    content = await _make_content(db, learner_user)
    with patch(
        "app.services.anthropic_client.send_structured",
        AsyncMock(side_effect=AnthropicClientError("boom")),
    ):
        flags = await grammar_service.run_check(db, content, "The dogs runs across the yard.")
    assert flags == []


async def test_attempt_fix_correct_rewrite_marks_self_corrected(db, learner_user):
    content = await _make_content(db, learner_user)
    with patch(
        "app.services.anthropic_client.send_structured",
        _mock_judgments([{"index": 1, "violates": True, "concept_id": "subject_verb_agreement"}]),
    ):
        flags = await grammar_service.run_check(db, content, "The dogs runs across the yard.")
    flag = flags[0]

    with patch(
        "app.services.anthropic_client.send_structured",
        _mock_judgments([{"index": 1, "violates": False, "concept_id": ""}]),
    ):
        updated = await grammar_service.attempt_fix(db, flag, "The dogs run across the yard.")
    assert updated.status == GrammarFlagStatus.self_corrected
    assert updated.resolved_at is not None


async def test_attempt_fix_wrong_rewrite_increments_without_reveal(db, learner_user):
    content = await _make_content(db, learner_user)
    with patch(
        "app.services.anthropic_client.send_structured",
        _mock_judgments([{"index": 1, "violates": True, "concept_id": "subject_verb_agreement"}]),
    ):
        flags = await grammar_service.run_check(db, content, "The dogs runs across the yard.")
    flag = flags[0]

    with patch(
        "app.services.anthropic_client.send_structured",
        _mock_judgments([{"index": 1, "violates": True, "concept_id": "subject_verb_agreement"}]),
    ):
        for expected_count in (1, 2, 3):
            flag = await grammar_service.attempt_fix(db, flag, "The dogs is running.")
            assert flag.attempt_count == expected_count
            assert flag.status == GrammarFlagStatus.pending


async def test_attempt_fix_llm_failure_does_not_consume_attempt(db, learner_user):
    content = await _make_content(db, learner_user)
    with patch(
        "app.services.anthropic_client.send_structured",
        _mock_judgments([{"index": 1, "violates": True, "concept_id": "subject_verb_agreement"}]),
    ):
        flags = await grammar_service.run_check(db, content, "The dogs runs across the yard.")
    flag = flags[0]

    with patch(
        "app.services.anthropic_client.send_structured",
        AsyncMock(side_effect=AnthropicClientError("boom")),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await grammar_service.attempt_fix(db, flag, "The dogs run across the yard.")
    assert exc_info.value.status_code == 503

    refreshed = await grammar_service.get_flag(db, flag.id)
    assert refreshed.attempt_count == 0


async def test_override_requires_two_prior_attempts(db, learner_user):
    content = await _make_content(db, learner_user)
    with patch(
        "app.services.anthropic_client.send_structured",
        _mock_judgments([{"index": 1, "violates": True, "concept_id": "subject_verb_agreement"}]),
    ):
        flags = await grammar_service.run_check(db, content, "The dogs runs across the yard.")
    flag = flags[0]

    with pytest.raises(HTTPException) as exc_info:
        await grammar_service.override(db, flag)
    assert exc_info.value.status_code == 409

    with patch(
        "app.services.anthropic_client.send_structured",
        _mock_judgments([{"index": 1, "violates": True, "concept_id": "subject_verb_agreement"}]),
    ):
        flag = await grammar_service.attempt_fix(db, flag, "wrong one")
        flag = await grammar_service.attempt_fix(db, flag, "wrong two")

    resolved = await grammar_service.override(db, flag)
    assert resolved.status == GrammarFlagStatus.kept_as_is


async def test_kept_as_is_sentence_never_reflagged(db, learner_user):
    content = await _make_content(db, learner_user)
    with patch(
        "app.services.anthropic_client.send_structured",
        _mock_judgments([{"index": 1, "violates": True, "concept_id": "subject_verb_agreement"}]),
    ):
        flags = await grammar_service.run_check(db, content, "The dogs runs across the yard.")
    flag = flags[0]

    with patch(
        "app.services.anthropic_client.send_structured",
        _mock_judgments([{"index": 1, "violates": True, "concept_id": "subject_verb_agreement"}]),
    ):
        flag = await grammar_service.attempt_fix(db, flag, "wrong one")
        flag = await grammar_service.attempt_fix(db, flag, "wrong two")
    await grammar_service.override(db, flag)

    with patch(
        "app.services.anthropic_client.send_structured",
        _mock_judgments([{"index": 1, "violates": True, "concept_id": "subject_verb_agreement"}]),
    ):
        flags_again = await grammar_service.run_check(db, content, "The dogs runs across the yard.")
    assert flags_again == []


async def test_self_corrected_reopens_if_same_sentence_reflagged(db, learner_user):
    content = await _make_content(db, learner_user)
    with patch(
        "app.services.anthropic_client.send_structured",
        _mock_judgments([{"index": 1, "violates": True, "concept_id": "subject_verb_agreement"}]),
    ):
        flags = await grammar_service.run_check(db, content, "The dogs runs across the yard.")
    flag = flags[0]
    with patch(
        "app.services.anthropic_client.send_structured",
        _mock_judgments([{"index": 1, "violates": False, "concept_id": ""}]),
    ):
        await grammar_service.attempt_fix(db, flag, "The dogs run across the yard.")

    with patch(
        "app.services.anthropic_client.send_structured",
        _mock_judgments([{"index": 1, "violates": True, "concept_id": "subject_verb_agreement"}]),
    ):
        flags_again = await grammar_service.run_check(db, content, "The dogs runs across the yard.")
    assert len(flags_again) == 1
    assert flags_again[0].status == GrammarFlagStatus.pending
    assert flags_again[0].attempt_count == 0


def _token_for(user, role: str) -> str:
    from app.core.security import create_access_token

    return create_access_token(str(user.id), email=user.email, name=user.name, role=role)


async def test_check_grammar_route_happy_path(client, db, learner_user):
    content = await _make_content(db, learner_user)
    token = _token_for(learner_user, "learner")

    with patch(
        "app.services.anthropic_client.send_structured",
        _mock_judgments([{"index": 1, "violates": True, "concept_id": "subject_verb_agreement"}]),
    ):
        response = client.post(
            f"/api/v1/content/{content.id}/grammar/check",
            json={"text": "The dogs runs across the yard."},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["concept_id"] == "subject_verb_agreement"
    assert body[0]["concept_label"] == "Subject and verb agreement"
    assert len(body[0]["example_pairs"]) == 2


async def test_check_grammar_route_rejects_non_owner(client, db, admin_user, learner_user):
    content = await _make_content(db, learner_user)
    other_token = _token_for(admin_user, "admin")

    response = client.post(
        f"/api/v1/content/{content.id}/grammar/check",
        json={"text": "The dogs runs across the yard."},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert response.status_code == 403


async def test_attempt_and_override_routes(client, db, learner_user):
    content = await _make_content(db, learner_user)
    token = _token_for(learner_user, "learner")
    headers = {"Authorization": f"Bearer {token}"}

    with patch(
        "app.services.anthropic_client.send_structured",
        _mock_judgments([{"index": 1, "violates": True, "concept_id": "subject_verb_agreement"}]),
    ):
        check_response = client.post(
            f"/api/v1/content/{content.id}/grammar/check",
            json={"text": "The dogs runs across the yard."},
            headers=headers,
        )
    flag_id = check_response.json()[0]["id"]

    with patch(
        "app.services.anthropic_client.send_structured",
        _mock_judgments([{"index": 1, "violates": False, "concept_id": ""}]),
    ):
        attempt_response = client.post(
            f"/api/v1/content/{content.id}/grammar/flags/{flag_id}/attempt",
            json={"sentence": "The dogs run across the yard."},
            headers=headers,
        )
    assert attempt_response.status_code == 200
    assert attempt_response.json()["status"] == "self_corrected"

    list_response = client.get(f"/api/v1/content/{content.id}/grammar/flags", headers=headers)
    assert list_response.json() == []


async def test_flag_from_another_content_404s(client, db, learner_user):
    content_a = await _make_content(db, learner_user)
    content_b = await _make_content(db, learner_user)
    token = _token_for(learner_user, "learner")
    headers = {"Authorization": f"Bearer {token}"}

    with patch(
        "app.services.anthropic_client.send_structured",
        _mock_judgments([{"index": 1, "violates": True, "concept_id": "subject_verb_agreement"}]),
    ):
        check_response = client.post(
            f"/api/v1/content/{content_a.id}/grammar/check",
            json={"text": "The dogs runs across the yard."},
            headers=headers,
        )
    flag_id = check_response.json()[0]["id"]

    response = client.post(
        f"/api/v1/content/{content_b.id}/grammar/flags/{flag_id}/attempt",
        json={"sentence": "The dogs run across the yard."},
        headers=headers,
    )
    assert response.status_code == 404
