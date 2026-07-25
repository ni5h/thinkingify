import pytest
from fastapi import HTTPException

from app.models.family_link import FamilyLinkStatus
from app.services import family_service


async def test_send_request_target_role_child_orients_sender_as_guardian(db, admin_user, learner_user):
    link = await family_service.send_request(db, admin_user, learner_user.email, "child")
    assert link.guardian_id == admin_user.id
    assert link.child_id == learner_user.id
    assert link.requested_by == admin_user.id
    assert link.status == FamilyLinkStatus.pending


async def test_send_request_target_role_guardian_orients_sender_as_child(db, admin_user, learner_user):
    link = await family_service.send_request(db, learner_user, admin_user.email, "guardian")
    assert link.guardian_id == admin_user.id
    assert link.child_id == learner_user.id
    assert link.requested_by == learner_user.id


async def test_send_request_to_unknown_email_raises_404(db, admin_user):
    with pytest.raises(HTTPException) as exc_info:
        await family_service.send_request(db, admin_user, "nobody@example.com", "child")
    assert exc_info.value.status_code == 404


async def test_send_request_to_self_raises_400(db, admin_user):
    with pytest.raises(HTTPException) as exc_info:
        await family_service.send_request(db, admin_user, admin_user.email, "child")
    assert exc_info.value.status_code == 400


async def test_send_request_duplicate_raises_409(db, admin_user, learner_user):
    await family_service.send_request(db, admin_user, learner_user.email, "child")
    with pytest.raises(HTTPException) as exc_info:
        await family_service.send_request(db, admin_user, learner_user.email, "child")
    assert exc_info.value.status_code == 409


async def test_list_incoming_and_outgoing(db, admin_user, learner_user):
    await family_service.send_request(db, admin_user, learner_user.email, "child")

    admin_outgoing = await family_service.list_outgoing(db, admin_user)
    assert len(admin_outgoing) == 1

    learner_incoming = await family_service.list_incoming(db, learner_user)
    assert len(learner_incoming) == 1

    admin_incoming = await family_service.list_incoming(db, admin_user)
    assert admin_incoming == []
    learner_outgoing = await family_service.list_outgoing(db, learner_user)
    assert learner_outgoing == []


async def test_accept_by_non_requester_succeeds(db, admin_user, learner_user):
    link = await family_service.send_request(db, admin_user, learner_user.email, "child")
    accepted = await family_service.accept(db, link.id, learner_user)
    assert accepted.status == FamilyLinkStatus.accepted
    assert accepted.accepted_at is not None


async def test_accept_by_requester_raises_403(db, admin_user, learner_user):
    link = await family_service.send_request(db, admin_user, learner_user.email, "child")
    with pytest.raises(HTTPException) as exc_info:
        await family_service.accept(db, link.id, admin_user)
    assert exc_info.value.status_code == 403


async def test_accept_non_pending_raises_409(db, admin_user, learner_user):
    link = await family_service.send_request(db, admin_user, learner_user.email, "child")
    await family_service.accept(db, link.id, learner_user)
    with pytest.raises(HTTPException) as exc_info:
        await family_service.accept(db, link.id, learner_user)
    assert exc_info.value.status_code == 409


async def test_decline_deletes_row(db, admin_user, learner_user):
    link = await family_service.send_request(db, admin_user, learner_user.email, "child")
    await family_service.decline(db, link.id, learner_user)

    outgoing = await family_service.list_outgoing(db, admin_user)
    assert outgoing == []
    # row is gone entirely, not just marked declined — re-request should succeed
    await family_service.send_request(db, admin_user, learner_user.email, "child")


async def test_decline_by_requester_raises_403(db, admin_user, learner_user):
    link = await family_service.send_request(db, admin_user, learner_user.email, "child")
    with pytest.raises(HTTPException) as exc_info:
        await family_service.decline(db, link.id, admin_user)
    assert exc_info.value.status_code == 403


async def test_list_my_links_only_includes_accepted(db, admin_user, learner_user, author_user):
    pending = await family_service.send_request(db, admin_user, learner_user.email, "child")
    accepted = await family_service.send_request(db, admin_user, author_user.email, "child")
    await family_service.accept(db, accepted.id, author_user)

    as_guardian, as_child = await family_service.list_my_links(db, admin_user)
    assert len(as_guardian) == 1
    assert as_guardian[0].child_id == author_user.id
    assert as_child == []
    assert pending.id != accepted.id  # sanity: two distinct links created


async def test_unlink_removes_accepted_link(db, admin_user, learner_user):
    link = await family_service.send_request(db, admin_user, learner_user.email, "child")
    await family_service.accept(db, link.id, learner_user)

    await family_service.unlink(db, link.id, admin_user)

    as_guardian, _ = await family_service.list_my_links(db, admin_user)
    assert as_guardian == []


async def test_unlink_pending_link_raises_409(db, admin_user, learner_user):
    link = await family_service.send_request(db, admin_user, learner_user.email, "child")
    with pytest.raises(HTTPException) as exc_info:
        await family_service.unlink(db, link.id, admin_user)
    assert exc_info.value.status_code == 409


async def test_is_accepted_guardian_and_has_any_accepted_guardian(db, admin_user, learner_user):
    assert not await family_service.is_accepted_guardian(db, admin_user.id, learner_user.id)
    assert not await family_service.has_any_accepted_guardian(db, learner_user.id)

    link = await family_service.send_request(db, admin_user, learner_user.email, "child")
    assert not await family_service.is_accepted_guardian(db, admin_user.id, learner_user.id)

    await family_service.accept(db, link.id, learner_user)
    assert await family_service.is_accepted_guardian(db, admin_user.id, learner_user.id)
    assert await family_service.has_any_accepted_guardian(db, learner_user.id)


async def test_assert_accepted_guardian_of_unknown_child_raises_404(db, admin_user):
    import uuid

    with pytest.raises(HTTPException) as exc_info:
        await family_service.assert_accepted_guardian_of(db, admin_user, uuid.uuid4())
    assert exc_info.value.status_code == 404


async def test_assert_accepted_guardian_of_non_guardian_raises_403(db, admin_user, learner_user):
    with pytest.raises(HTTPException) as exc_info:
        await family_service.assert_accepted_guardian_of(db, admin_user, learner_user.id)
    assert exc_info.value.status_code == 403


async def test_assert_accepted_guardian_of_succeeds_when_accepted(db, admin_user, learner_user):
    link = await family_service.send_request(db, admin_user, learner_user.email, "child")
    await family_service.accept(db, link.id, learner_user)

    child = await family_service.assert_accepted_guardian_of(db, admin_user, learner_user.id)
    assert child.id == learner_user.id


def _token_for(user, role: str) -> str:
    from app.core.security import create_access_token

    return create_access_token(str(user.id), email=user.email, name=user.name, role=role)


def test_family_requests_endpoint_requires_authentication(client):
    response = client.post("/api/v1/family/requests", json={"email": "x@example.com", "target_role": "child"})
    assert response.status_code in (401, 403)


def test_send_and_accept_request_via_api(client, admin_user, learner_user):
    admin_token = _token_for(admin_user, "admin")
    learner_token = _token_for(learner_user, "learner")

    create_resp = client.post(
        "/api/v1/family/requests",
        json={"email": learner_user.email, "target_role": "child"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_resp.status_code == 201
    link_id = create_resp.json()["id"]
    assert create_resp.json()["guardian"]["email"] == admin_user.email
    assert create_resp.json()["child"]["email"] == learner_user.email

    accept_resp = client.post(
        f"/api/v1/family/requests/{link_id}/accept", headers={"Authorization": f"Bearer {learner_token}"}
    )
    assert accept_resp.status_code == 200
    assert accept_resp.json()["status"] == "accepted"


def test_child_summary_endpoint_rejects_non_guardian(client, admin_user, learner_user):
    admin_token = _token_for(admin_user, "admin")
    response = client.get(
        f"/api/v1/family/children/{learner_user.id}/summary", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 403


def test_child_summary_endpoint_succeeds_for_accepted_guardian(client, admin_user, learner_user):
    admin_token = _token_for(admin_user, "admin")
    learner_token = _token_for(learner_user, "learner")

    create_resp = client.post(
        "/api/v1/family/requests",
        json={"email": learner_user.email, "target_role": "child"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    link_id = create_resp.json()["id"]
    client.post(f"/api/v1/family/requests/{link_id}/accept", headers={"Authorization": f"Bearer {learner_token}"})

    response = client.get(
        f"/api/v1/family/children/{learner_user.id}/summary", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["child_name"] == learner_user.name
    assert body["total_puzzle_attempts"] == 0
    assert body["published_post_count"] == 0
