import uuid

from app.core.security import create_access_token


def _auth(user):
    return {"Authorization": f"Bearer {create_access_token(str(user.id), email=user.email, name=user.name, role=user.role.value)}"}


def _make_live_concept(client, admin_user, n=5):
    code = "m" + uuid.uuid4().hex[:6]
    subj = client.post("/api/v1/admin/curriculum/subjects", json={"name": "M", "code": code, "grade": 4}, headers=_auth(admin_user)).json()
    ch = client.post("/api/v1/admin/curriculum/chapters", json={"subject_id": subj["id"], "title": "Big"}, headers=_auth(admin_user)).json()
    con = client.post("/api/v1/admin/curriculum/concepts", json={"chapter_id": ch["id"], "title": "PV"}, headers=_auth(admin_user)).json()
    for i in range(n):
        item = client.post(
            "/api/v1/admin/curriculum/items",
            json={"concept_id": con["id"], "kind": "recall", "difficulty": 2, "body": f"Q{i}", "answer_key": "A"},
            headers=_auth(admin_user),
        ).json()
        client.post(f"/api/v1/admin/curriculum/items/{item['id']}/submit-for-review", headers=_auth(admin_user))
        client.post(f"/api/v1/admin/curriculum/items/{item['id']}/accept", headers=_auth(admin_user))
    return ch, con


def test_check_item_never_exposes_level_or_answer_key(client, admin_user, learner_user):
    _, con = _make_live_concept(client, admin_user)
    start = client.post(
        f"/api/v1/curriculum/concepts/{con['id']}/check/start",
        json={"think_results": ["right", "wrong"]},
        headers=_auth(learner_user),
    )
    assert start.status_code == 200
    item = start.json()["item"]
    assert set(item.keys()) <= {"id", "concept_id", "kind", "body", "options"}
    assert "difficulty" not in item and "answer_key" not in item


def test_wrong_answer_is_non_punitive(client, admin_user, learner_user):
    _, con = _make_live_concept(client, admin_user)
    start = client.post(f"/api/v1/curriculum/concepts/{con['id']}/check/start", json={"think_results": []}, headers=_auth(learner_user)).json()
    ans = client.post(
        f"/api/v1/curriculum/check/{start['session_id']}/answer",
        json={"item_id": start["item"]["id"], "choice": "B", "unsure": False, "hint_used": False},
        headers=_auth(learner_user),
    )
    assert ans.status_code == 200
    body = ans.json()
    assert body["correct"] is False
    assert body["reveal_answer"] == "A"
    assert "score" not in body and "level" not in body
    assert "hint" in body and "source_asset_id" in body  # the gentle feedback keys


def test_progress_reports_states_not_numbers(client, admin_user, learner_user):
    ch, con = _make_live_concept(client, admin_user)
    prog = client.get(f"/api/v1/curriculum/chapters/{ch['id']}/progress", headers=_auth(learner_user))
    assert prog.status_code == 200
    rows = prog.json()
    assert len(rows) == 1
    assert rows[0]["state"] in {"learning", "solid", "needs_look"}
    assert rows[0]["available"] is True  # no prerequisites
    assert "level" not in rows[0] and "difficulty" not in rows[0]


def test_check_routes_require_auth(client, admin_user):
    _, con = _make_live_concept(client, admin_user)
    assert client.post(f"/api/v1/curriculum/concepts/{con['id']}/check/start", json={}).status_code in (401, 403)
