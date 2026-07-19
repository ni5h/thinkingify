from app.schemas.topic import TopicCreate
from app.services import note_service, topic_service


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
