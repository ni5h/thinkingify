from app.core.security import create_access_token


def _token(user) -> str:
    return create_access_token(str(user.id), email=user.email, name=user.name, role=user.role.value)


def _auth(user):
    return {"Authorization": f"Bearer {_token(user)}"}


def test_admin_write_requires_admin(client, admin_user, learner_user):
    body = {"name": "Maths", "code": "maths", "grade": 4}
    assert client.post("/api/v1/admin/curriculum/subjects", json=body, headers=_auth(learner_user)).status_code == 403
    r = client.post("/api/v1/admin/curriculum/subjects", json=body, headers=_auth(admin_user))
    assert r.status_code == 201


def test_admin_read_requires_admin(client, learner_user):
    assert client.get("/api/v1/admin/curriculum/subjects", headers=_auth(learner_user)).status_code == 403


def _make_item(client, admin_user):
    subj = client.post("/api/v1/admin/curriculum/subjects", json={"name": "M", "code": "m1", "grade": 4}, headers=_auth(admin_user)).json()
    ch = client.post("/api/v1/admin/curriculum/chapters", json={"subject_id": subj["id"], "title": "Big Numbers"}, headers=_auth(admin_user)).json()
    con = client.post("/api/v1/admin/curriculum/concepts", json={"chapter_id": ch["id"], "title": "Place value"}, headers=_auth(admin_user)).json()
    item = client.post("/api/v1/admin/curriculum/items", json={"concept_id": con["id"], "kind": "apply", "body": "2+2?", "answer_key": "4"}, headers=_auth(admin_user)).json()
    return con, item


def test_learner_curriculum_hides_nonlive_and_answer_key(client, admin_user, learner_user):
    con, item = _make_item(client, admin_user)

    # Draft item is invisible to a learner.
    live = client.get(f"/api/v1/curriculum/concepts/{con['id']}/items", headers=_auth(learner_user))
    assert live.status_code == 200 and live.json() == []

    # Move it to live.
    client.post(f"/api/v1/admin/curriculum/items/{item['id']}/submit-for-review", headers=_auth(admin_user))
    client.post(f"/api/v1/admin/curriculum/items/{item['id']}/accept", headers=_auth(admin_user))

    live = client.get(f"/api/v1/curriculum/concepts/{con['id']}/items", headers=_auth(learner_user)).json()
    assert len(live) == 1
    # answer_key must never reach the learner.
    assert "answer_key" not in live[0]
    # ...but the admin view includes it.
    admin_view = client.get(f"/api/v1/admin/curriculum/items/{item['id']}", headers=_auth(admin_user)).json()
    assert admin_view["answer_key"] == "4"


def test_illegal_transition_returns_409(client, admin_user):
    _con, item = _make_item(client, admin_user)
    # accept from draft is illegal
    r = client.post(f"/api/v1/admin/curriculum/items/{item['id']}/accept", headers=_auth(admin_user))
    assert r.status_code == 409


def test_review_queue_lists_draft_items(client, admin_user):
    _con, item = _make_item(client, admin_user)
    queue = client.get("/api/v1/admin/curriculum/review", headers=_auth(admin_user)).json()
    assert item["id"] in [i["id"] for i in queue]


def test_admin_emails_grant_admin_role_on_login(monkeypatch):
    from app.models.user import UserRole
    from app.services import auth_service

    monkeypatch.setattr(auth_service.settings, "admin_emails", "Boss@Thinkingify.dev")
    assert auth_service._role_for("boss@thinkingify.dev") == UserRole.admin  # case-insensitive
    assert auth_service._role_for("kid@thinkingify.dev") == UserRole.learner
