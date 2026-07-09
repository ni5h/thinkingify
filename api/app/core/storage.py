import io
import uuid

from fastapi import HTTPException, UploadFile, status
from PIL import Image
from supabase import Client, create_client

from app.core.config import settings

_MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5MB


def _supabase() -> Client:
    return create_client(settings.supabase_url, settings.supabase_anon_key)


async def upload_feature_image(file: UploadFile) -> str:
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File must be an image.")

    raw = await file.read()
    if len(raw) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Image must be under 5MB.")

    try:
        # Re-encode server-side rather than trusting the client's declared
        # content-type or its own compression — defense in depth for a
        # backend-proxied upload path a spoofed client could otherwise abuse.
        image = Image.open(io.BytesIO(raw))
        image = image.convert("RGB")
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=80)
        jpeg_bytes = buffer.getvalue()
    except Exception as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Could not decode image.") from exc

    # Not nested under a content id: the editor lets an author pick a feature
    # image before the post has ever been saved (and thus has no id yet), so
    # the upload endpoint is decoupled from any particular post.
    path = f"feature-images/{uuid.uuid4()}.jpg"
    client = _supabase()
    client.storage.from_(settings.supabase_storage_bucket).upload(
        path, jpeg_bytes, {"content-type": "image/jpeg"}
    )
    return client.storage.from_(settings.supabase_storage_bucket).get_public_url(path)
