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


def _make_chapter_with_content(client, admin_user):
    """A chapter with one concept, two draft items, and two draft assets."""
    a = _auth(admin_user)
    subj = client.post("/api/v1/admin/curriculum/subjects", json={"name": "E", "code": "evs1", "grade": 4}, headers=a).json()
    ch = client.post("/api/v1/admin/curriculum/chapters", json={"subject_id": subj["id"], "title": "Animals"}, headers=a).json()
    con = client.post("/api/v1/admin/curriculum/concepts", json={"chapter_id": ch["id"], "title": "Groups"}, headers=a).json()
    for body in ("q1", "q2"):
        client.post("/api/v1/admin/curriculum/items", json={"concept_id": con["id"], "kind": "apply", "body": body, "answer_key": "x"}, headers=a)
    for kind in ("card", "recap"):
        client.post("/api/v1/admin/curriculum/assets", json={"concept_id": con["id"], "kind": kind, "body": "b"}, headers=a)
    return ch, con


def test_chapter_content_summary_counts_drafts(client, admin_user):
    ch, con = _make_chapter_with_content(client, admin_user)
    summary = client.get(f"/api/v1/admin/curriculum/chapters/{ch['id']}/content", headers=_auth(admin_user)).json()
    assert summary["item_totals"]["draft"] == 2
    assert summary["asset_totals"]["draft"] == 2
    assert summary["publishable_count"] == 4
    assert summary["live_count"] == 0
    assert summary["concepts"][0]["concept_id"] == con["id"]


def test_publish_chapter_takes_items_and_assets_live(client, admin_user, learner_user):
    ch, con = _make_chapter_with_content(client, admin_user)
    # One item is already at "reviewed" — publish must take that live too.
    first_item = client.get("/api/v1/admin/curriculum/items", params={"concept_id": con["id"]}, headers=_auth(admin_user)).json()[0]
    client.post(f"/api/v1/admin/curriculum/items/{first_item['id']}/submit-for-review", headers=_auth(admin_user))

    result = client.post(f"/api/v1/admin/curriculum/chapters/{ch['id']}/publish", headers=_auth(admin_user))
    assert result.status_code == 200
    assert result.json() == {"items": 2, "assets": 2}

    # Learner now sees live content (previously hidden).
    live_items = client.get(f"/api/v1/curriculum/concepts/{con['id']}/items", headers=_auth(learner_user)).json()
    live_assets = client.get(f"/api/v1/curriculum/concepts/{con['id']}/assets", headers=_auth(learner_user)).json()
    assert len(live_items) == 2
    assert len(live_assets) == 2

    # Publishing again is a no-op (nothing left in draft/reviewed).
    again = client.post(f"/api/v1/admin/curriculum/chapters/{ch['id']}/publish", headers=_auth(admin_user)).json()
    assert again == {"items": 0, "assets": 0}


def test_retire_chapter_unpublishes_live(client, admin_user, learner_user):
    ch, con = _make_chapter_with_content(client, admin_user)
    client.post(f"/api/v1/admin/curriculum/chapters/{ch['id']}/publish", headers=_auth(admin_user))
    result = client.post(f"/api/v1/admin/curriculum/chapters/{ch['id']}/retire", headers=_auth(admin_user)).json()
    assert result == {"items": 2, "assets": 2}
    live_items = client.get(f"/api/v1/curriculum/concepts/{con['id']}/items", headers=_auth(learner_user)).json()
    assert live_items == []


def test_chapter_publish_requires_admin(client, admin_user, learner_user):
    ch, _con = _make_chapter_with_content(client, admin_user)
    assert client.post(f"/api/v1/admin/curriculum/chapters/{ch['id']}/publish", headers=_auth(learner_user)).status_code == 403
    assert client.get(f"/api/v1/admin/curriculum/chapters/{ch['id']}/content", headers=_auth(learner_user)).status_code == 403


def test_admin_emails_grant_admin_role_on_login(monkeypatch):
    from app.models.user import UserRole
    from app.services import auth_service

    monkeypatch.setattr(auth_service.settings, "admin_emails", "Boss@Thinkingify.dev")
    assert auth_service._role_for("boss@thinkingify.dev") == UserRole.admin  # case-insensitive
    assert auth_service._role_for("kid@thinkingify.dev") == UserRole.learner
