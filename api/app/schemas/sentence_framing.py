import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.sentence_framing_flag import SentenceFramingFlagStatus


class SentenceFramingCheckRequest(BaseModel):
    # A list, not a flat string, so detection can be scoped per Rowling
    # section — a flagged run must never span a section boundary, or the
    # correction-application find-and-replace can't locate it in either
    # editor. A single-element list for the blank/post-editor case.
    sections: list[str] = Field(..., min_length=1, max_length=50)


class SentenceFramingAttemptRequest(BaseModel):
    sentences: str = Field(..., min_length=1, max_length=2000)


class ExamplePairOut(BaseModel):
    incorrect: str
    correct: str


class SentenceFramingFlagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    content_id: uuid.UUID
    concept_id: str
    sentences: str
    status: SentenceFramingFlagStatus
    attempt_count: int
    created_at: datetime
    # Resolved from the concept bank at response-assembly time (see
    # sentence_framing_service.to_out) — same pattern as GrammarFlagOut.
    concept_label: str = ""
    concept_rule: str = ""
    example_pairs: list[ExamplePairOut] = Field(default_factory=list)
