import io
import uuid

from fastapi import HTTPException, UploadFile, status
from PIL import Image
from supabase import Client, create_client

from app.core.config import settings

_MAX_UPLOAD_IMAGE_BYTES = 5 * 1024 * 1024  # 5MB
_MAX_UPLOAD_AUDIO_BYTES = 20 * 1024 * 1024  # 20MB


def _supabase() -> Client:
    return create_client(settings.supabase_url, settings.supabase_anon_key)


async def upload_image(file: UploadFile, path_prefix: str) -> str:
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File must be an image.")

    raw = await file.read()
    if len(raw) > _MAX_UPLOAD_IMAGE_BYTES:
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

    path = f"{path_prefix}/{uuid.uuid4()}.jpg"
    client = _supabase()
    client.storage.from_(settings.supabase_storage_bucket).upload(
        path, jpeg_bytes, {"content-type": "image/jpeg"}
    )
    return client.storage.from_(settings.supabase_storage_bucket).get_public_url(path)


async def upload_feature_image(file: UploadFile) -> str:
    # Not nested under a content id: the editor lets an author pick a feature
    # image before the post has ever been saved (and thus has no id yet), so
    # the upload endpoint is decoupled from any particular post.
    return await upload_image(file, "feature-images")


async def upload_topic_image(file: UploadFile) -> str:
    return await upload_image(file, "topic-images")


async def upload_topic_audio(file: UploadFile) -> str:
    if not (file.content_type or "").startswith("audio/"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File must be audio.")

    raw = await file.read()
    if len(raw) > _MAX_UPLOAD_AUDIO_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Audio must be under 20MB.")

    # No re-encoding — Pillow can't touch audio, so raw bytes go straight
    # through as-is (unlike images, which get re-encoded for defense in
    # depth against a spoofed content-type).
    ext = (file.content_type or "audio/mpeg").split("/")[-1].split(";")[0] or "mp3"
    path = f"topic-audio/{uuid.uuid4()}.{ext}"
    client = _supabase()
    client.storage.from_(settings.supabase_storage_bucket).upload(
        path, raw, {"content-type": file.content_type or "audio/mpeg"}
    )
    return client.storage.from_(settings.supabase_storage_bucket).get_public_url(path)
