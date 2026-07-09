from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.services.auth_service import _resolve_role, google_sign_in
from app.models.user import UserRole


def test_admin_email_resolves_to_admin_role():
    assert _resolve_role("admin@example.com") == UserRole.admin


def test_author_email_resolves_to_author_role():
    assert _resolve_role("author@example.com") == UserRole.author


def test_email_case_insensitive():
    assert _resolve_role("Admin@Example.com") == UserRole.admin


def test_unlisted_email_raises_403():
    with pytest.raises(HTTPException) as exc_info:
        _resolve_role("stranger@example.com")
    assert exc_info.value.status_code == 403


async def test_google_sign_in_unlisted_email_creates_no_user(db):
    def fake_verify(token, request, client_id):
        return {"sub": "sub-1", "email": "stranger@example.com", "name": "Stranger"}

    with patch("app.services.auth_service.google_id_token.verify_oauth2_token", side_effect=fake_verify):
        with pytest.raises(HTTPException) as exc_info:
            await google_sign_in("fake-token", db)
    assert exc_info.value.status_code == 403

    from sqlalchemy import select
    from app.models.user import User

    result = await db.execute(select(User))
    assert result.scalars().all() == []


async def test_google_sign_in_admin_email_creates_admin_user(db):
    def fake_verify(token, request, client_id):
        return {"sub": "sub-2", "email": "admin@example.com", "name": "Admin"}

    with patch("app.services.auth_service.google_id_token.verify_oauth2_token", side_effect=fake_verify):
        response = await google_sign_in("fake-token", db)

    assert response.user.role == UserRole.admin
    assert response.access_token
    assert response.refresh_token


async def test_google_sign_in_role_re_resolved_on_repeat_login(db):
    """If ADMIN_EMAILS/AUTHOR_EMAILS changes, an existing user's role updates
    on their next login rather than requiring a manual promotion step."""

    def fake_verify(token, request, client_id):
        return {"sub": "sub-3", "email": "author@example.com", "name": "Author"}

    with patch("app.services.auth_service.google_id_token.verify_oauth2_token", side_effect=fake_verify):
        first = await google_sign_in("fake-token", db)
    assert first.user.role == UserRole.author

    with patch("app.core.config.settings.author_emails", ""), patch(
        "app.core.config.settings.admin_emails", "author@example.com"
    ):
        with patch(
            "app.services.auth_service.google_id_token.verify_oauth2_token", side_effect=fake_verify
        ):
            second = await google_sign_in("fake-token", db)
    assert second.user.role == UserRole.admin
    assert second.user.id == first.user.id
