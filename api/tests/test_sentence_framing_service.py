import pytest
from fastapi import HTTPException

from app.models.sentence_framing_flag import SentenceFramingFlagStatus
from app.schemas.content import ContentCreate
from app.services import content_service, sentence_framing_service


async def _make_content(db, author, style="blank"):
    return await content_service.create(
        db, author, ContentCreate(title="My Story", content_markdown="", style=style)
    )


# Longer sentences than a natural repeated-opening example might use,
# deliberately: every sentence is well above the choppy-run word
# threshold, so this fixture only ever trips repeated_sentence_openings,
# never choppy_short_sentences too — keeps each concept's tests isolated.
_REPEATED_I = (
    "I really wanted to go to the park today. "
    "I quickly saw a friendly dog running around. "
    "I happily threw a bright red ball for it."
)
_REPEATED_I_FIXED = (
    "I really wanted to go to the park today. "
    "There, I quickly saw a friendly dog running around. "
    "Excited, I happily threw a bright red ball for it."
)
_CHOPPY = "The dog ran. It was fast. I laughed."


async def test_repeated_openings_flagged_at_three_in_a_row(db, learner_user):
    content = await _make_content(db, learner_user)
    flags = await sentence_framing_service.run_check(db, content, [_REPEATED_I])
    assert len(flags) == 1
    assert flags[0].concept_id == "repeated_sentence_openings"
    assert flags[0].sentences == _REPEATED_I
    assert flags[0].status == SentenceFramingFlagStatus.pending


async def test_two_in_a_row_not_flagged(db, learner_user):
    content = await _make_content(db, learner_user)
    flags = await sentence_framing_service.run_check(
        db, content, ["I went to the park. I saw a dog. We had fun together that day."]
    )
    assert flags == []


async def test_choppy_short_sentences_flagged(db, learner_user):
    content = await _make_content(db, learner_user)
    flags = await sentence_framing_service.run_check(db, content, [_CHOPPY])
    assert len(flags) == 1
    assert flags[0].concept_id == "choppy_short_sentences"

    out = sentence_framing_service.to_out(flags[0])
    assert out.concept_label == "Combining short sentences"
    assert len(out.example_pairs) == 1


async def test_how_to_style_skips_choppy_check(db, learner_user):
    content = await _make_content(db, learner_user, style="how_to")
    flags = await sentence_framing_service.run_check(db, content, [_CHOPPY])
    assert flags == []


async def test_section_boundary_isolation_prevents_cross_section_run(db, learner_user):
    """A run that would exist if the two sections were flattened together
    must NOT be detected when passed as separate section texts — this is
    the core correctness guarantee that keeps correction-application
    (a literal substring find-and-replace within one editor) always able
    to find what it's fixing."""
    content = await _make_content(db, learner_user)
    section_1 = "It was a normal day. I woke up early."
    section_2 = "I brushed my teeth. I ate breakfast fast."
    # Flattened, "I woke up early. I brushed my teeth. I ate breakfast
    # fast." would be a 3-in-a-row "I" run spanning the boundary.
    flags = await sentence_framing_service.run_check(db, content, [section_1, section_2])
    assert flags == []


async def test_run_within_a_single_section_still_detected_alongside_others(db, learner_user):
    content = await _make_content(db, learner_user)
    flags = await sentence_framing_service.run_check(db, content, ["Just a normal sentence here.", _REPEATED_I])
    assert len(flags) == 1
    assert flags[0].sentences == _REPEATED_I


async def test_attempt_fix_breaking_pattern_marks_self_corrected(db, learner_user):
    content = await _make_content(db, learner_user)
    flags = await sentence_framing_service.run_check(db, content, [_REPEATED_I])
    flag = flags[0]

    rewritten = _REPEATED_I_FIXED
    updated = await sentence_framing_service.attempt_fix(db, flag, rewritten)
    assert updated.status == SentenceFramingFlagStatus.self_corrected
    assert updated.resolved_at is not None


async def test_attempt_fix_still_matching_increments_without_reveal(db, learner_user):
    content = await _make_content(db, learner_user)
    flags = await sentence_framing_service.run_check(db, content, [_REPEATED_I])
    flag = flags[0]

    for expected_count in (1, 2, 3):
        flag = await sentence_framing_service.attempt_fix(db, flag, _REPEATED_I)
        assert flag.attempt_count == expected_count
        assert flag.status == SentenceFramingFlagStatus.pending


async def test_override_requires_two_prior_attempts(db, learner_user):
    content = await _make_content(db, learner_user)
    flags = await sentence_framing_service.run_check(db, content, [_REPEATED_I])
    flag = flags[0]

    with pytest.raises(HTTPException) as exc_info:
        await sentence_framing_service.override(db, flag)
    assert exc_info.value.status_code == 409

    flag = await sentence_framing_service.attempt_fix(db, flag, _REPEATED_I)
    flag = await sentence_framing_service.attempt_fix(db, flag, _REPEATED_I)
    resolved = await sentence_framing_service.override(db, flag)
    assert resolved.status == SentenceFramingFlagStatus.kept_as_is


async def test_kept_as_is_never_reflagged(db, learner_user):
    content = await _make_content(db, learner_user)
    flags = await sentence_framing_service.run_check(db, content, [_REPEATED_I])
    flag = flags[0]
    flag = await sentence_framing_service.attempt_fix(db, flag, _REPEATED_I)
    flag = await sentence_framing_service.attempt_fix(db, flag, _REPEATED_I)
    await sentence_framing_service.override(db, flag)

    flags_again = await sentence_framing_service.run_check(db, content, [_REPEATED_I])
    assert flags_again == []


async def test_self_corrected_reopens_if_same_run_reappears(db, learner_user):
    content = await _make_content(db, learner_user)
    flags = await sentence_framing_service.run_check(db, content, [_REPEATED_I])
    flag = flags[0]
    rewritten = _REPEATED_I_FIXED
    await sentence_framing_service.attempt_fix(db, flag, rewritten)

    flags_again = await sentence_framing_service.run_check(db, content, [_REPEATED_I])
    assert len(flags_again) == 1
    assert flags_again[0].status == SentenceFramingFlagStatus.pending
    assert flags_again[0].attempt_count == 0


def _token_for(user, role: str) -> str:
    from app.core.security import create_access_token

    return create_access_token(str(user.id), email=user.email, name=user.name, role=role)


async def test_check_sentence_framing_route_happy_path(client, db, learner_user):
    content = await _make_content(db, learner_user)
    token = _token_for(learner_user, "learner")

    response = client.post(
        f"/api/v1/content/{content.id}/sentence-framing/check",
        json={"sections": [_REPEATED_I]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["concept_id"] == "repeated_sentence_openings"
    assert body[0]["concept_label"] == "Varying your sentence openings"


async def test_check_sentence_framing_route_rejects_non_owner(client, db, admin_user, learner_user):
    content = await _make_content(db, learner_user)
    other_token = _token_for(admin_user, "admin")

    response = client.post(
        f"/api/v1/content/{content.id}/sentence-framing/check",
        json={"sections": [_REPEATED_I]},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert response.status_code == 403


async def test_attempt_and_override_routes(client, db, learner_user):
    content = await _make_content(db, learner_user)
    token = _token_for(learner_user, "learner")
    headers = {"Authorization": f"Bearer {token}"}

    check_response = client.post(
        f"/api/v1/content/{content.id}/sentence-framing/check",
        json={"sections": [_REPEATED_I]},
        headers=headers,
    )
    flag_id = check_response.json()[0]["id"]

    rewritten = _REPEATED_I_FIXED
    attempt_response = client.post(
        f"/api/v1/content/{content.id}/sentence-framing/flags/{flag_id}/attempt",
        json={"sentences": rewritten},
        headers=headers,
    )
    assert attempt_response.status_code == 200
    assert attempt_response.json()["status"] == "self_corrected"

    list_response = client.get(f"/api/v1/content/{content.id}/sentence-framing/flags", headers=headers)
    assert list_response.json() == []


async def test_flag_from_another_content_404s(client, db, learner_user):
    content_a = await _make_content(db, learner_user)
    content_b = await _make_content(db, learner_user)
    token = _token_for(learner_user, "learner")
    headers = {"Authorization": f"Bearer {token}"}

    check_response = client.post(
        f"/api/v1/content/{content_a.id}/sentence-framing/check",
        json={"sections": [_REPEATED_I]},
        headers=headers,
    )
    flag_id = check_response.json()[0]["id"]

    response = client.post(
        f"/api/v1/content/{content_b.id}/sentence-framing/flags/{flag_id}/attempt",
        json={"sentences": _REPEATED_I},
        headers=headers,
    )
    assert response.status_code == 404
