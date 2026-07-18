import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NoteUpdate(BaseModel):
    body: str


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    topic_id: uuid.UUID
    user_id: uuid.UUID
    body: str
    updated_at: datetime
