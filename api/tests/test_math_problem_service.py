import uuid

import pytest
from fastapi import HTTPException

from app.models.math_problem import MathAnswerKind, MathProblemStatus
from app.schemas.math import MathProblemCreate
from app.services import math_problem_service


async def _make_problem(db, author, *, answer="42", kind=MathAnswerKind.integer, solution="Because.", title="A problem"):
    return await math_problem_service.create(
        db,
        author,
        MathProblemCreate(
            title=title,
            statement_markdown="What is the answer?",
            answer=answer,
            answer_kind=kind,
            solution_markdown=solution,
            concept_tags=["patterns"],
            difficulty=2,
        ),
    )


async def test_create_defaults_to_draft_with_slug(db, learner_user):
    problem = await _make_problem(db, learner_user, title="The Growing Gaps")
    assert problem.slug == "the-growing-gaps"
    assert problem.status == MathProblemStatus.draft
    assert problem.author_id == learner_user.id


async def test_publish_requires_answer_and_solution(db, learner_user):
    no_answer = await _make_problem(db, learner_user, answer="", title="No answer")
    with pytest.raises(HTTPException) as exc:
        await math_problem_service.transition(db, no_answer, "publish")
    assert exc.value.status_code == 400

    no_solution = await _make_problem(db, learner_user, solution="", title="No solution")
    with pytest.raises(HTTPException) as exc:
        await math_problem_service.transition(db, no_solution, "publish")
    assert exc.value.status_code == 400

    good = await _make_problem(db, learner_user, title="Good one")
    published = await math_problem_service.transition(db, good, "publish")
    assert published.status == MathProblemStatus.published
    assert published.published_at is not None


@pytest.mark.parametrize(
    "answer,kind,submitted,expected",
    [
        ("42", MathAnswerKind.integer, "42", True),
        ("42", MathAnswerKind.integer, " 42 ", True),
        ("1000", MathAnswerKind.integer, "1,000", True),
        ("42", MathAnswerKind.integer, "43", False),
        ("42", MathAnswerKind.integer, "forty-two", False),
        ("6", MathAnswerKind.integer, "six", False),
        ("prime", MathAnswerKind.text, "Prime", True),
        ("prime", MathAnswerKind.text, "  prime  ", True),
        ("prime", MathAnswerKind.text, "composite", False),
    ],
)
def test_check_answer_normalization(answer, kind, submitted, expected):
    from app.models.math_problem import MathProblem

    problem = MathProblem(id=uuid.uuid4(), title="t", slug="t", answer=answer, answer_kind=kind)
    assert math_problem_service.check_answer(problem, submitted) is expected


async def test_record_attempt_logs_server_computed_correctness(db, learner_user):
    problem = await _make_problem(db, learner_user, answer="42")

    wrong = await math_problem_service.record_attempt(db, learner_user, problem, "41")
    assert wrong.is_correct is False

    right = await math_problem_service.record_attempt(db, learner_user, problem, "42")
    assert right.is_correct is True


async def test_list_published_only_returns_published(db, learner_user):
    draft = await _make_problem(db, learner_user, title="Draft one")
    published = await _make_problem(db, learner_user, title="Published one")
    await math_problem_service.transition(db, published, "publish")

    listed = await math_problem_service.list_published(db)
    ids = {p.id for p in listed}
    assert published.id in ids
    assert draft.id not in ids


def _token_for(user, role: str) -> str:
    from app.core.security import create_access_token

    return create_access_token(str(user.id), email=user.email, name=user.name, role=role)


async def test_public_schemas_never_expose_answer_or_solution(client, db, learner_user):
    problem = await _make_problem(db, learner_user, answer="42", solution="Secret working.")
    await math_problem_service.transition(db, problem, "publish")

    # Public list
    list_resp = client.get("/api/v1/math/problems/published")
    assert list_resp.status_code == 200
    body = list_resp.json()[0]
    assert "answer" not in body
    assert "solution_markdown" not in body

    # Public single
    one_resp = client.get(f"/api/v1/math/problems/published/{problem.slug}")
    assert one_resp.status_code == 200
    one = one_resp.json()
    assert "answer" not in one
    assert "solution_markdown" not in one
    assert one["statement_markdown"] == "What is the answer?"


async def test_attempt_route_reveals_solution_only_when_correct(client, db, learner_user):
    problem = await _make_problem(db, learner_user, answer="42", solution="Here is the neat way.")
    await math_problem_service.transition(db, problem, "publish")
    token = _token_for(learner_user, "learner")
    headers = {"Authorization": f"Bearer {token}"}

    wrong = client.post(
        f"/api/v1/math/problems/{problem.id}/attempts", json={"submitted_answer": "41"}, headers=headers
    )
    assert wrong.status_code == 200
    assert wrong.json()["is_correct"] is False
    assert wrong.json()["solution_markdown"] is None

    right = client.post(
        f"/api/v1/math/problems/{problem.id}/attempts", json={"submitted_answer": "42"}, headers=headers
    )
    assert right.status_code == 200
    assert right.json()["is_correct"] is True
    assert right.json()["solution_markdown"] == "Here is the neat way."


async def test_author_gated_routes_reject_non_owner(client, db, learner_user, admin_user):
    problem = await _make_problem(db, learner_user)
    other = _token_for(admin_user, "admin")

    resp = client.patch(
        f"/api/v1/math/problems/{problem.id}",
        json={"title": "hijack"},
        headers={"Authorization": f"Bearer {other}"},
    )
    assert resp.status_code == 403
