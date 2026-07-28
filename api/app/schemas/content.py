import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.models.content import ContentStatus
from app.schemas.user import UserPublicSummary

WritingStyle = Literal["fairy_tale", "news_report", "diary_entry", "letter", "how_to", "blank"]


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
    # Deliberately str, not WritingStyle — this is the read path and must
    # never fail to serialize a value stored before the style set last
    # changed (WritingStyle is enforced on writes only, see ContentCreate/
    # ContentUpdate above).
    style: str | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime
    # Only populated by the public-facing list_published/get_published_by_slug
    # paths (see content_service._attach_authors) — Content has no ORM
    # attribute for this, so it defaults to None everywhere else (owner-
    # facing Studio routes just `return content` and never render a byline).
    author: UserPublicSummary | None = None


class ContentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    slug: str
    summary: str | None
    feature_image_url: str | None
    status: ContentStatus
    topic_id: uuid.UUID | None
    style: str | None
    published_at: datetime | None
    updated_at: datetime
    author: UserPublicSummary | None = None
