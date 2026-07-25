import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.models.family_link import FamilyLinkStatus

TargetRole = Literal["guardian", "child"]


class FamilyLinkRequestCreate(BaseModel):
    email: str
    target_role: TargetRole


class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
    avatar_url: str | None


class FamilyLinkOut(BaseModel):
    id: uuid.UUID
    status: FamilyLinkStatus
    requested_by: uuid.UUID
    guardian: UserSummary
    child: UserSummary
    created_at: datetime
    accepted_at: datetime | None


class FamilyLinksOut(BaseModel):
    as_guardian: list[FamilyLinkOut]
    as_child: list[FamilyLinkOut]


class ChildSummaryOut(BaseModel):
    """Compact stats for a guardian's dashboard card — effort-focused
    counts, not a full activity feed. See ui/CLAUDE.md's "no accuracy%,
    no comparisons" rule, which applies here too."""

    child_id: uuid.UUID
    child_name: str
    total_puzzle_attempts: int
    puzzle_attempts_this_week: int
    published_post_count: int
