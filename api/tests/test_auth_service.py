from unittest.mock import patch

from sqlalchemy import select

from app.models.user import User, UserRole
from app.schemas.user import ProfileUpdate
from app.services import user_service
from app.services.auth_service import DEV_USER_NAME, dev_login, google_sign_in


async def test_google_sign_in_creates_user_for_any_email(db):
    """Open sign-up: a previously-unseen email still gets a User row and
    working tokens, not a 403 — there's no allow-list anymore."""

    def fake_verify(token, request, client_id):
        return {"sub": "sub-1", "email": "stranger@example.com", "name": "Stranger"}

    with patch("app.services.auth_service.google_id_token.verify_oauth2_token", side_effect=fake_verify):
        response = await google_sign_in("fake-token", db)

    assert response.user.email == "stranger@example.com"
    assert response.access_token
    assert response.refresh_token


async def test_google_sign_in_reuses_same_user_on_repeat_login(db):
    def fake_verify(token, request, client_id):
        return {"sub": "sub-2", "email": "someone@example.com", "name": "Someone"}

    with patch("app.services.auth_service.google_id_token.verify_oauth2_token", side_effect=fake_verify):
        first = await google_sign_in("fake-token", db)
        second = await google_sign_in("fake-token", db)

    assert first.user.id == second.user.id


async def test_google_sign_in_does_not_clobber_customized_profile_on_relogin(db):
    """A user who's set a custom first_name/avatar_url via the Profile
    page shouldn't have it silently overwritten by their next Google
    login, even if their Google name/picture changed in the meantime."""

    def fake_verify_first(token, request, client_id):
        return {"sub": "sub-3", "email": "grows@example.com", "name": "Original Name", "picture": "https://orig/pic.jpg"}

    with patch("app.services.auth_service.google_id_token.verify_oauth2_token", side_effect=fake_verify_first):
        first = await google_sign_in("fake-token", db)

    user = (await db.execute(select(User).where(User.id == first.user.id))).scalar_one()
    await user_service.update_profile(
        db, user, ProfileUpdate(first_name="Custom", avatar_url="https://custom/avatar.jpg")
    )

    def fake_verify_second(token, request, client_id):
        return {"sub": "sub-3", "email": "grows@example.com", "name": "Changed Name", "picture": "https://changed/pic.jpg"}

    with patch("app.services.auth_service.google_id_token.verify_oauth2_token", side_effect=fake_verify_second):
        second = await google_sign_in("fake-token", db)

    assert second.user.name == "Original Name"
    assert second.user.avatar_url == "https://custom/avatar.jpg"


async def test_dev_login_creates_user_named_nish(db):
    response = await dev_login(db)
    assert response.user.name == DEV_USER_NAME
    assert response.user.role == UserRole.learner
    assert response.access_token


async def test_dev_login_reuses_same_user_on_repeat_call(db):
    first = await dev_login(db)
    second = await dev_login(db)
    assert first.user.id == second.user.id


def test_dev_login_route_rejected_when_disabled(client):
    with patch("app.core.config.settings.allow_dev_login", False):
        response = client.post("/api/v1/auth/dev-login")
    assert response.status_code == 403


def test_dev_login_route_succeeds_when_enabled(client):
    with patch("app.core.config.settings.allow_dev_login", True):
        response = client.post("/api/v1/auth/dev-login")
    assert response.status_code == 200
    assert response.json()["user"]["name"] == DEV_USER_NAME
