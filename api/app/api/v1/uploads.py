from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from app.core.deps import require_author_or_admin
from app.core.storage import upload_feature_image
from app.models.user import User

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/feature-image")
async def upload(
    current_user: Annotated[User, Depends(require_author_or_admin)],
    file: Annotated[UploadFile, File()],
):
    url = await upload_feature_image(file)
    return {"url": url}
