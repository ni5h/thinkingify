from app.schemas.content import ContentCreate
from app.schemas.topic import TopicCreate
from app.services import content_service, note_service, topic_service


async def _blank_post(db, author):
    return await content_service.create(
        db, author, ContentCreate(title="", content_markdown="", topic_id=None, style="blank")
    )


async def test_get_or_create_for_content_creates_empty_note(db, learner_user):
    post = await _blank_post(db, learner_user)
    note = await note_service.get_or_create_for_content(db, learner_user, post.id)
    assert note.body == ""
    assert note.content_id == post.id
    assert note.topic_id is None
    assert note.user_id == learner_user.id


async def test_get_or_create_for_content_reuses_existing_note(db, learner_user):
    post = await _blank_post(db, learner_user)
    first = await note_service.get_or_create_for_content(db, learner_user, post.id)
    await note_service.update(db, first, "brainstorm")

    second = await note_service.get_or_create_for_content(db, learner_user, post.id)
    assert second.id == first.id
    assert second.body == "brainstorm"


async def test_content_notes_endpoint_round_trip(client, learner_user):
    from app.core.security import create_access_token

    token = create_access_token(str(learner_user.id), email=learner_user.email, name=learner_user.name, role="learner")
    headers = {"Authorization": f"Bearer {token}"}
    create_resp = client.post("/api/v1/content", json={"title": "", "content_markdown": "", "style": "blank"}, headers=headers)
    content_id = create_resp.json()["id"]

    patch_resp = client.patch(f"/api/v1/content/{content_id}/notes", json={"body": "my ideas"}, headers=headers)
    assert patch_resp.status_code == 200
    assert patch_resp.json()["body"] == "my ideas"
    assert patch_resp.json()["content_id"] == content_id

    get_resp = client.get(f"/api/v1/content/{content_id}/notes", headers=headers)
    assert get_resp.json()["body"] == "my ideas"


async def test_get_or_create_creates_empty_note_on_first_access(db, admin_user, learner_user):
    topic = await topic_service.create(db, admin_user, TopicCreate(title="A Topic"))
    note = await note_service.get_or_create(db, learner_user, topic.id)
    assert note.body == ""
    assert note.topic_id == topic.id
    assert note.user_id == learner_user.id


async def test_get_or_create_reuses_existing_note(db, admin_user, learner_user):
    topic = await topic_service.create(db, admin_user, TopicCreate(title="A Topic"))
    first = await note_service.get_or_create(db, learner_user, topic.id)
    await note_service.update(db, first, "some notes")

    second = await note_service.get_or_create(db, learner_user, topic.id)
    assert second.id == first.id
    assert second.body == "some notes"


async def test_notes_are_scoped_per_user(db, admin_user, learner_user):
    topic = await topic_service.create(db, admin_user, TopicCreate(title="A Topic"))
    learner_note = await note_service.get_or_create(db, learner_user, topic.id)
    await note_service.update(db, learner_note, "learner's notes")

    admin_note = await note_service.get_or_create(db, admin_user, topic.id)
    assert admin_note.id != learner_note.id
    assert admin_note.body == ""


def _token_for(user, role: str) -> str:
    from app.core.security import create_access_token

    return create_access_token(str(user.id), email=user.email, name=user.name, role=role)


def test_notes_endpoint_autosave_round_trip(client, admin_user, learner_user):
    admin_token = _token_for(admin_user, "admin")
    create_resp = client.post(
        "/api/v1/topics", json={"title": "A Topic"}, headers={"Authorization": f"Bearer {admin_token}"}
    )
    topic_id = create_resp.json()["id"]

    learner_token = _token_for(learner_user, "learner")
    patch_resp = client.patch(
        f"/api/v1/topics/{topic_id}/notes",
        json={"body": "my scribbles"},
        headers={"Authorization": f"Bearer {learner_token}"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["body"] == "my scribbles"

    get_resp = client.get(f"/api/v1/topics/{topic_id}/notes", headers={"Authorization": f"Bearer {learner_token}"})
    assert get_resp.json()["body"] == "my scribbles"


def test_notes_endpoint_works_for_any_authenticated_user(client, admin_user, author_user):
    """No more role gate — notes just require authentication, same as
    everything else."""
    admin_token = _token_for(admin_user, "admin")
    create_resp = client.post(
        "/api/v1/topics", json={"title": "A Topic"}, headers={"Authorization": f"Bearer {admin_token}"}
    )
    topic_id = create_resp.json()["id"]

    author_token = _token_for(author_user, "author")
    response = client.get(f"/api/v1/topics/{topic_id}/notes", headers={"Authorization": f"Bearer {author_token}"})
    assert response.status_code == 200
