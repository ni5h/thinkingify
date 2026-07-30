import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.grammar_flag import GrammarFlagStatus


class GrammarCheckRequest(BaseModel):
    text: str = Field(..., max_length=20000)


class GrammarAttemptRequest(BaseModel):
    sentence: str = Field(..., min_length=1, max_length=2000)


class ExamplePairOut(BaseModel):
    incorrect: str
    correct: str


class GrammarFlagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    content_id: uuid.UUID
    concept_id: str
    sentence: str
    status: GrammarFlagStatus
    attempt_count: int
    created_at: datetime
    # Resolved from the concept bank at response-assembly time (see
    # grammar_service.to_out) — not real columns on GrammarFlag, hence the
    # defaults so model_validate(orm_object) succeeds before model_copy
    # fills these in with the real values.
    concept_label: str = ""
    concept_rule: str = ""
    example_pairs: list[ExamplePairOut] = Field(default_factory=list)
