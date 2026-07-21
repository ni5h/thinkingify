import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.models.content import ContentStatus

WritingStyle = Literal["documentary", "story", "fun_casual", "freeform"]


class ContentCreate(BaseModel):
    title: str
    summary: str | None = None
    content_markdown: str = ""
    topic_id: uuid.UUID | None = None
    style: WritingStyle | None = None


class ContentUpdate(BaseModel):
    title: str | None = None
    summary: str | None = None
    content_markdown: str | None = None
    feature_image_url: str | None = None
    topic_id: uuid.UUID | None = None
    style: WritingStyle | None = None


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
    topic_id: uuid.UUID | None
    style: WritingStyle | None
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
    topic_id: uuid.UUID | None
    style: WritingStyle | None
    published_at: datetime | None
    updated_at: datetime
