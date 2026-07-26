import io
from unittest.mock import MagicMock, patch

from PIL import Image


def _token_for(user, role: str) -> str:
    from app.core.security import create_access_token

    return create_access_token(str(user.id), email=user.email, name=user.name, role=role)


def _fake_png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), color="red").save(buffer, format="PNG")
    return buffer.getvalue()


def test_upload_avatar_rejects_non_image_content_type(client, admin_user):
    token = _token_for(admin_user, "admin")
    response = client.post(
        "/api/v1/uploads/avatar",
        files={"file": ("avatar.txt", b"not an image", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400


def test_upload_avatar_rejects_oversized_file(client, admin_user):
    token = _token_for(admin_user, "admin")
    oversized = b"0" * (5 * 1024 * 1024 + 1)
    response = client.post(
        "/api/v1/uploads/avatar",
        files={"file": ("avatar.png", oversized, "image/png")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400


def test_upload_avatar_succeeds(client, admin_user):
    token = _token_for(admin_user, "admin")

    fake_client = MagicMock()
    fake_client.storage.from_.return_value.get_public_url.return_value = "https://fake.supabase.co/avatars/x.jpg"

    with patch("app.core.storage._supabase", return_value=fake_client):
        response = client.post(
            "/api/v1/uploads/avatar",
            files={"file": ("avatar.png", _fake_png_bytes(), "image/png")},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["url"] == "https://fake.supabase.co/avatars/x.jpg"
    fake_client.storage.from_.return_value.upload.assert_called_once()
    upload_path = fake_client.storage.from_.return_value.upload.call_args[0][0]
    assert upload_path.startswith("avatars/")
