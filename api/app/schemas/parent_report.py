import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ParentReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    content_id: uuid.UUID
    word_count: int
    headline: str
    creativity_narrative: str
    suggested_action: str | None
    went_well: list[str]
    was_tricky: list[str]
    stage_breakdown: dict
    ai_help_level: str
    created_at: datetime
    # Joined from Content at response-assembly time, not stored on the
    # row — same denormalize-at-read pattern as content_service.py's
    # ContentOut author join.
    content_title: str = ""
    style: str | None = None
