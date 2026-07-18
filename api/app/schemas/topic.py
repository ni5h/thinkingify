import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.topic import TopicStatus


class TopicCreate(BaseModel):
    title: str
    explainer_markdown: str = ""
    audio_url: str | None = None
    order_index: int = 0


class TopicUpdate(BaseModel):
    title: str | None = None
    explainer_markdown: str | None = None
    audio_url: str | None = None
    order_index: int | None = None


class TopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    slug: str
    explainer_markdown: str
    audio_url: str | None
    status: TopicStatus
    order_index: int
    author_id: uuid.UUID
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TopicListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    slug: str
    status: TopicStatus
    order_index: int
    updated_at: datetime
