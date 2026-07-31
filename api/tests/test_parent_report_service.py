import uuid
from unittest.mock import AsyncMock, patch

from app.models.companion_message import CompanionMessage, CompanionMessageRole
from app.models.grammar_flag import GrammarFlag, GrammarFlagStatus
from app.models.sentence_framing_flag import SentenceFramingFlag, SentenceFramingFlagStatus
from app.models.spelling_flag import SpellingErrorType, SpellingFlag, SpellingFlagStatus
from app.schemas.content import ContentCreate
from app.services import content_service, family_service, parent_report_service
from app.services.anthropic_client import AnthropicClientError


async def _make_post(db, author, title="My Story", style="blank"):
    return await content_service.create(
        db, author, ContentCreate(title=title, content_markdown="Once upon a time.", style=style)
    )


async def _link_guardian(db, guardian, child):
    link = await family_service.send_request(db, child, guardian.email, "guardian")
    await family_service.accept(db, link.id, guardian)


def _mock_narrative(headline="Test headline.", creativity="Test creativity.", action=""):
    return AsyncMock(
        return_value={"headline": headline, "creativity_narrative": creativity, "suggested_action": action}
    )


async def _add_spelling_flag(db, content_id, word, status, hint_revealed=False):
    flag = SpellingFlag(
        id=uuid.uuid4(),
        content_id=content_id,
        word=word,
        error_type=SpellingErrorType.misspelling,
        context_sentence=word,
        status=status,
        hint_revealed=hint_revealed,
    )
    db.add(flag)
    await db.commit()
    return flag


async def _add_grammar_flag(db, content_id, concept_id, sentence, status):
    flag = GrammarFlag(
        id=uuid.uuid4(), content_id=content_id, concept_id=concept_id, sentence=sentence, status=status
    )
    db.add(flag)
    await db.commit()
    return flag


async def _add_framing_flag(db, content_id, concept_id, sentences, status):
    flag = SentenceFramingFlag(
        id=uuid.uuid4(), content_id=content_id, concept_id=concept_id, sentences=sentences, status=status
    )
    db.add(flag)
    await db.commit()
    return flag


async def _add_companion_message(db, content_id, user_id, ladder_level=1, direct_answer_requested=False):
    msg = CompanionMessage(
        id=uuid.uuid4(),
        content_id=content_id,
        user_id=user_id,
        session_id=uuid.uuid4(),
        role=CompanionMessageRole.assistant,
        body="reply",
        ladder_level=ladder_level,
        direct_answer_requested=direct_answer_requested,
    )
    db.add(msg)
    await db.commit()
    return msg


async def test_stage_breakdown_aggregates_across_all_three_stages(db, learner_user):
    content = await _make_post(db, learner_user)
    await _add_spelling_flag(db, content.id, "hopeing", SpellingFlagStatus.self_corrected, hint_revealed=True)
    await _add_spelling_flag(db, content.id, "zzyzx", SpellingFlagStatus.kept_as_is)
    await _add_grammar_flag(db, content.id, "subject_verb_agreement", "The dogs runs.", GrammarFlagStatus.self_corrected)
    await _add_framing_flag(
        db, content.id, "repeated_sentence_openings", "I went. I saw. I left.", SentenceFramingFlagStatus.self_corrected
    )

    with patch("app.services.anthropic_client.send_structured", _mock_narrative()):
        report = await parent_report_service.generate_report(db, content)

    assert report.stage_breakdown["spelling"]["found"] == 2
    assert report.stage_breakdown["spelling"]["self_corrected"] == 1
    assert report.stage_breakdown["spelling"]["kept_as_is"] == 1
    assert report.stage_breakdown["spelling"]["ai_assisted"] == 1
    assert "hopeing" in report.stage_breakdown["spelling"]["concepts"]

    assert report.stage_breakdown["grammar"]["found"] == 1
    assert report.stage_breakdown["grammar"]["self_corrected"] == 1
    assert report.stage_breakdown["grammar"]["ai_assisted"] == 0
    assert "Subject and verb agreement" in report.stage_breakdown["grammar"]["concepts"]

    assert report.stage_breakdown["sentence_framing"]["found"] == 1
    assert "Varying your sentence openings" in report.stage_breakdown["sentence_framing"]["concepts"]


async def test_ai_assisted_proxy_only_fires_for_spelling(db, learner_user):
    content = await _make_post(db, learner_user)
    # hint_revealed but NOT self_corrected shouldn't count as ai_assisted.
    await _add_spelling_flag(db, content.id, "wrd", SpellingFlagStatus.kept_as_is, hint_revealed=True)
    await _add_grammar_flag(db, content.id, "run_on_sentence", "A run on.", GrammarFlagStatus.self_corrected)

    with patch("app.services.anthropic_client.send_structured", _mock_narrative()):
        report = await parent_report_service.generate_report(db, content)

    assert report.stage_breakdown["spelling"]["ai_assisted"] == 0
    assert report.stage_breakdown["grammar"]["ai_assisted"] == 0


async def test_ai_help_level_tiers(db, learner_user):
    content = await _make_post(db, learner_user)

    with patch("app.services.anthropic_client.send_structured", _mock_narrative()):
        independent = await parent_report_service.generate_report(db, content)
    assert "independently" in independent.ai_help_level

    await _add_companion_message(db, content.id, learner_user.id, ladder_level=3)
    with patch("app.services.anthropic_client.send_structured", _mock_narrative()):
        nudged = await parent_report_service.generate_report(db, content)
    assert "occasional nudges" in nudged.ai_help_level

    for _ in range(3):
        await _add_companion_message(db, content.id, learner_user.id, direct_answer_requested=True)
    with patch("app.services.anthropic_client.send_structured", _mock_narrative()):
        supported = await parent_report_service.generate_report(db, content)
    assert "more support" in supported.ai_help_level


async def test_narrative_fails_soft_on_anthropic_error(db, learner_user):
    content = await _make_post(db, learner_user, title="Fallback Test")
    await _add_grammar_flag(db, content.id, "sentence_fragment", "Broken.", GrammarFlagStatus.self_corrected)

    with patch("app.services.anthropic_client.send_structured", AsyncMock(side_effect=AnthropicClientError("boom"))):
        report = await parent_report_service.generate_report(db, content)

    assert "Fallback Test" in report.headline
    assert report.suggested_action is None
    assert report.creativity_narrative
    # Templated sections are entirely unaffected by the LLM failure.
    assert report.stage_breakdown["grammar"]["found"] == 1


async def test_report_generated_on_submit_for_review_without_blocking_response(client, db, learner_user, admin_user):
    await _link_guardian(db, admin_user, learner_user)
    content = await _make_post(db, learner_user)

    from app.core.security import create_access_token

    token = create_access_token(str(learner_user.id), email=learner_user.email, name=learner_user.name, role="learner")

    with patch("app.services.anthropic_client.send_structured", AsyncMock(side_effect=AnthropicClientError("boom"))):
        response = client.post(
            f"/api/v1/content/{content.id}/submit-for-review", headers={"Authorization": f"Bearer {token}"}
        )
    assert response.status_code == 200
    assert response.json()["status"] == "pending_review"

    reports = await parent_report_service.list_for_child(db, learner_user.id)
    assert len(reports) == 1
    assert reports[0].content_id == content.id


async def test_resubmission_creates_a_second_report(db, learner_user):
    content = await _make_post(db, learner_user)
    with patch("app.services.anthropic_client.send_structured", _mock_narrative()):
        await parent_report_service.generate_report(db, content)
        await parent_report_service.generate_report(db, content)

    reports = await parent_report_service.list_for_child(db, learner_user.id)
    assert len(reports) == 2


def _token_for(user, role: str) -> str:
    from app.core.security import create_access_token

    return create_access_token(str(user.id), email=user.email, name=user.name, role=role)


async def test_child_reports_route_guardian_only(client, db, learner_user, admin_user):
    content = await _make_post(db, learner_user)
    with patch("app.services.anthropic_client.send_structured", _mock_narrative()):
        await parent_report_service.generate_report(db, content)

    # Unrelated user: 403.
    other_token = _token_for(admin_user, "admin")
    response = client.get(f"/api/v1/family/children/{learner_user.id}/reports", headers={"Authorization": f"Bearer {other_token}"})
    assert response.status_code == 403

    # The child themself is not a guardian of themself: 403.
    own_token = _token_for(learner_user, "learner")
    response = client.get(
        f"/api/v1/family/children/{learner_user.id}/reports", headers={"Authorization": f"Bearer {own_token}"}
    )
    assert response.status_code == 403

    # Accepted guardian: 200.
    await _link_guardian(db, admin_user, learner_user)
    response = client.get(f"/api/v1/family/children/{learner_user.id}/reports", headers={"Authorization": f"Bearer {other_token}"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["content_title"] == "My Story"


async def test_single_report_route_404s_for_mismatched_child(client, db, learner_user, admin_user):
    await _link_guardian(db, admin_user, learner_user)
    other_child = admin_user  # reuse as a second, unrelated "child" id for the mismatch check
    content = await _make_post(db, learner_user)
    with patch("app.services.anthropic_client.send_structured", _mock_narrative()):
        report = await parent_report_service.generate_report(db, content)

    guardian_token = _token_for(admin_user, "admin")
    response = client.get(
        f"/api/v1/family/children/{other_child.id}/reports/{report.id}",
        headers={"Authorization": f"Bearer {guardian_token}"},
    )
    assert response.status_code in (403, 404)
