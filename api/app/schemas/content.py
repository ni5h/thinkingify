import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.content import ContentStatus


class ContentCreate(BaseModel):
    title: str
    summary: str | None = None
    content_markdown: str = ""


class ContentUpdate(BaseModel):
    title: str | None = None
    summary: str | None = None
    content_markdown: str | None = None
    feature_image_url: str | None = None


class ContentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    slug: str
    summary: str | None
    content_markdown: str
    feature_image_url: str | None
    status: ContentStatus
    author_id: uuid.UUID
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ContentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    slug: str
    summary: str | None
    feature_image_url: str | None
    status: ContentStatus
    published_at: datetime | None
    updated_at: datetime
