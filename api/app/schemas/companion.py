import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.companion_message import CompanionMessageRole


class CompanionMessageCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=2000)
    session_id: uuid.UUID


class CompanionMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    content_id: uuid.UUID
    role: CompanionMessageRole
    body: str
    ladder_level: int | None
    direct_answer_requested: bool
    fact_leak_blocked: bool
    is_fallback: bool
    created_at: datetime
