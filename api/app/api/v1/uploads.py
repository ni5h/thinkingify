from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from app.core.deps import require_admin, require_author_or_admin
from app.core.storage import upload_feature_image, upload_topic_audio, upload_topic_image
from app.models.user import User

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/feature-image")
async def upload(
    current_user: Annotated[User, Depends(require_author_or_admin)],
    file: Annotated[UploadFile, File()],
):
    url = await upload_feature_image(file)
    return {"url": url}


@router.post("/topic-image")
async def upload_topic_image_endpoint(
    current_user: Annotated[User, Depends(require_admin)],
    file: Annotated[UploadFile, File()],
):
    url = await upload_topic_image(file)
    return {"url": url}


@router.post("/topic-audio")
async def upload_topic_audio_endpoint(
    current_user: Annotated[User, Depends(require_admin)],
    file: Annotated[UploadFile, File()],
):
    url = await upload_topic_audio(file)
    return {"url": url}
