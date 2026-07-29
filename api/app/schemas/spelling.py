import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.spelling_flag import SpellingErrorType, SpellingFlagStatus


class SpellingCheckRequest(BaseModel):
    text: str = Field(..., max_length=20000)


class SpellingAttemptRequest(BaseModel):
    word: str = Field(..., min_length=1, max_length=100)


class SpellingFlagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    content_id: uuid.UUID
    word: str
    error_type: SpellingErrorType
    context_sentence: str
    suggested_correction: str | None
    hint: str | None
    status: SpellingFlagStatus
    hint_revealed: bool
    attempt_count: int
    created_at: datetime
