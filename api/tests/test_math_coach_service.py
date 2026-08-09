import uuid
from unittest.mock import AsyncMock, patch

from app.models.math_coach_message import MathCoachMessageRole
from app.models.math_problem import MathAnswerKind
from app.schemas.math import MathProblemCreate
from app.services import math_coach_service, math_problem_service
from app.services.anthropic_client import AnthropicClientError


async def _make_problem(db, author, *, answer="42", solution="Add the gaps: 30 plus 12 gives the result."):
    return await math_problem_service.create(
        db,
        author,
        MathProblemCreate(
            title="A problem",
            statement_markdown="2, 6, 12, 20, 30, ?",
            answer=answer,
            answer_kind=MathAnswerKind.integer,
            solution_markdown=solution,
            concept_tags=["patterns"],
            difficulty=1,
        ),
    )


def _mock_reply(reply, ladder_level=1, asked_for_answer=False):
    return AsyncMock(
        return_value={"reply": reply, "ladder_level": ladder_level, "asked_for_answer": asked_for_answer}
    )


async def test_happy_path_persists_both_messages(db, learner_user):
    problem = await _make_problem(db, learner_user)
    session_id = uuid.uuid4()

    with patch(
        "app.services.anthropic_client.send_structured",
        _mock_reply("What do you notice about the gaps between the numbers?"),
    ):
        reply = await math_coach_service.send_message(db, learner_user, problem, session_id, "I'm stuck")

    assert reply.role == MathCoachMessageRole.assistant
    assert reply.is_fallback is False
    assert reply.body.endswith("?")

    history = await math_coach_service.list_messages(db, problem)
    assert len(history) == 2
    assert history[0].role == MathCoachMessageRole.user
    assert history[0].body == "I'm stuck"


async def test_missing_nudge_is_repaired(db, learner_user):
    problem = await _make_problem(db, learner_user)
    with patch("app.services.anthropic_client.send_structured", _mock_reply("Try the smaller numbers first.")):
        reply = await math_coach_service.send_message(db, learner_user, problem, uuid.uuid4(), "help")
    assert reply.body.strip().endswith("?")


async def test_ladder_cannot_jump_more_than_one_rung(db, learner_user):
    problem = await _make_problem(db, learner_user)
    session_id = uuid.uuid4()
    with patch("app.services.anthropic_client.send_structured", _mock_reply("Still stuck?", ladder_level=4)):
        first = await math_coach_service.send_message(db, learner_user, problem, session_id, "help")
    assert first.ladder_level == 2  # 1 + 1, not 4

    with patch("app.services.anthropic_client.send_structured", _mock_reply("Still stuck?", ladder_level=4)):
        second = await math_coach_service.send_message(db, learner_user, problem, session_id, "still stuck")
    assert second.ladder_level == 3


async def test_coach_blocks_bare_answer_leak(db, learner_user):
    problem = await _make_problem(db, learner_user, answer="42")
    session_id = uuid.uuid4()
    # The model tries to just hand over the answer number.
    with patch(
        "app.services.anthropic_client.send_structured",
        _mock_reply("The pattern means the next number is 42, well done."),
    ):
        reply = await math_coach_service.send_message(db, learner_user, problem, session_id, "what's the answer")

    assert reply.answer_leak_blocked is True
    assert "42" not in reply.body  # the leaking reply was replaced


async def test_coach_blocks_solution_prose_leak(db, learner_user):
    solution = "Add the gaps: 30 plus 12 gives the result you are looking for here."
    problem = await _make_problem(db, learner_user, answer="99", solution=solution)
    session_id = uuid.uuid4()
    # The model near-verbatim recites the worked solution (no bare answer).
    with patch(
        "app.services.anthropic_client.send_structured",
        _mock_reply("Here's how: add the gaps: 30 plus 12 gives the result you are looking for here."),
    ):
        reply = await math_coach_service.send_message(db, learner_user, problem, session_id, "hint please")

    assert reply.answer_leak_blocked is True


async def test_api_failure_returns_graceful_fallback(db, learner_user):
    problem = await _make_problem(db, learner_user)
    session_id = uuid.uuid4()
    with patch("app.services.anthropic_client.send_structured", _mock_reply("Level two.", ladder_level=2)):
        first = await math_coach_service.send_message(db, learner_user, problem, session_id, "help")
    assert first.ladder_level == 2

    with patch(
        "app.services.anthropic_client.send_structured", AsyncMock(side_effect=AnthropicClientError("boom"))
    ):
        second = await math_coach_service.send_message(db, learner_user, problem, session_id, "again")
    assert second.is_fallback is True
    assert second.ladder_level == 2  # unchanged, not reset


async def test_asked_for_answer_tracked(db, learner_user):
    problem = await _make_problem(db, learner_user)
    with patch(
        "app.services.anthropic_client.send_structured",
        _mock_reply("What could you try first?", asked_for_answer=True),
    ):
        reply = await math_coach_service.send_message(db, learner_user, problem, uuid.uuid4(), "just tell me")
    assert reply.asked_for_answer is True


def _token_for(user, role: str) -> str:
    from app.core.security import create_access_token

    return create_access_token(str(user.id), email=user.email, name=user.name, role=role)


async def test_coach_route_happy_path(client, db, learner_user):
    problem = await _make_problem(db, learner_user)
    token = _token_for(learner_user, "learner")
    with patch("app.services.anthropic_client.send_structured", _mock_reply("What do you notice?")):
        resp = client.post(
            f"/api/v1/math/problems/{problem.id}/coach/messages",
            json={"body": "hi", "session_id": str(uuid.uuid4())},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 201
    assert resp.json()["role"] == "assistant"
    # The coach's out-schema never carries answer/solution fields.
    assert "answer" not in resp.json()
