import uuid

import pytest
from fastapi import HTTPException

from app.services import family_service, user_service
from app.schemas.user import ProfileUpdate


async def test_update_profile_applies_partial_update(db, admin_user):
    updated = await user_service.update_profile(db, admin_user, ProfileUpdate(first_name="Ada"))
    assert updated.first_name == "Ada"
    assert updated.last_name is None


async def test_update_profile_leaves_unspecified_fields_untouched(db, admin_user):
    await user_service.update_profile(db, admin_user, ProfileUpdate(first_name="Ada", last_name="Lovelace"))
    updated = await user_service.update_profile(db, admin_user, ProfileUpdate(tagline="curious"))
    assert updated.first_name == "Ada"
    assert updated.last_name == "Lovelace"
    assert updated.tagline == "curious"


async def test_update_profile_username_normalized_via_slugify(db, admin_user):
    updated = await user_service.update_profile(db, admin_user, ProfileUpdate(username="  Ada Lovelace!  "))
    assert updated.username == "ada-lovelace"


async def test_update_profile_duplicate_username_raises_409(db, admin_user, learner_user):
    await user_service.update_profile(db, admin_user, ProfileUpdate(username="taken"))
    with pytest.raises(HTTPException) as exc_info:
        await user_service.update_profile(db, learner_user, ProfileUpdate(username="taken"))
    assert exc_info.value.status_code == 409


async def test_update_profile_same_user_can_resave_own_username(db, admin_user):
    await user_service.update_profile(db, admin_user, ProfileUpdate(username="ada"))
    updated = await user_service.update_profile(db, admin_user, ProfileUpdate(username="ada", tagline="hi"))
    assert updated.username == "ada"
    assert updated.tagline == "hi"


def test_profile_update_username_too_short_raises_422():
    with pytest.raises(ValueError):
        ProfileUpdate(username="ab")


async def test_public_summaries_by_id_display_name_fallback(db, admin_user, learner_user):
    await user_service.update_profile(db, admin_user, ProfileUpdate(username="ada"))
    await user_service.update_profile(db, learner_user, ProfileUpdate(first_name="Grace"))

    summaries = await user_service.public_summaries_by_id(db, {admin_user.id, learner_user.id})

    assert summaries[admin_user.id].display_name == "ada"
    assert summaries[learner_user.id].display_name == "Grace"
    assert not hasattr(summaries[admin_user.id], "last_name")
    assert not hasattr(summaries[admin_user.id], "email")


async def test_public_summaries_by_id_no_name_set_is_null(db, admin_user):
    summaries = await user_service.public_summaries_by_id(db, {admin_user.id})
    assert summaries[admin_user.id].display_name is None


async def test_assert_linked_allows_self(db, admin_user):
    result = await family_service.assert_linked(db, admin_user, admin_user.id)
    assert result.id == admin_user.id


async def test_assert_linked_allows_either_direction(db, admin_user, learner_user):
    link = await family_service.send_request(db, admin_user, learner_user.email, "child")
    await family_service.accept(db, link.id, learner_user)

    guardian_view = await family_service.assert_linked(db, admin_user, learner_user.id)
    assert guardian_view.id == learner_user.id
    child_view = await family_service.assert_linked(db, learner_user, admin_user.id)
    assert child_view.id == admin_user.id


async def test_assert_linked_unrelated_raises_403(db, admin_user, learner_user):
    with pytest.raises(HTTPException) as exc_info:
        await family_service.assert_linked(db, admin_user, learner_user.id)
    assert exc_info.value.status_code == 403


async def test_assert_linked_unknown_user_raises_404(db, admin_user):
    with pytest.raises(HTTPException) as exc_info:
        await family_service.assert_linked(db, admin_user, uuid.uuid4())
    assert exc_info.value.status_code == 404


def _token_for(user, role: str) -> str:
    from app.core.security import create_access_token

    return create_access_token(str(user.id), email=user.email, name=user.name, role=role)


def test_patch_me_route_happy_path(client, admin_user):
    token = _token_for(admin_user, "admin")
    response = client.patch(
        "/api/v1/auth/me",
        json={"first_name": "Ada", "account_type": "parent"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["first_name"] == "Ada"
    assert body["account_type"] == "parent"
    assert body["profile_completion_percent"] > 0


def test_patch_me_route_duplicate_username_returns_409(client, admin_user, learner_user):
    admin_token = _token_for(admin_user, "admin")
    learner_token = _token_for(learner_user, "learner")

    client.patch(
        "/api/v1/auth/me", json={"username": "shared"}, headers={"Authorization": f"Bearer {admin_token}"}
    )
    response = client.patch(
        "/api/v1/auth/me", json={"username": "shared"}, headers={"Authorization": f"Bearer {learner_token}"}
    )
    assert response.status_code == 409


def test_get_linked_profile_route_self(client, admin_user):
    token = _token_for(admin_user, "admin")
    response = client.get(f"/api/v1/users/{admin_user.id}/profile", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_get_linked_profile_route_unrelated_raises_403(client, admin_user, learner_user):
    token = _token_for(admin_user, "admin")
    response = client.get(f"/api/v1/users/{learner_user.id}/profile", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_get_linked_profile_route_unknown_user_raises_404(client, admin_user):
    token = _token_for(admin_user, "admin")
    response = client.get(f"/api/v1/users/{uuid.uuid4()}/profile", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
