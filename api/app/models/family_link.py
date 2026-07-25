import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class FamilyLinkStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"


class FamilyLink(Base, TimestampMixin):
    __tablename__ = "family_links"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guardian_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    child_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    # Orientation (who's the guardian, who's the child) is decided at
    # request time by which of two actions the sender picked — there's no
    # separate role column. requested_by always equals the sender, and is
    # what restricts accept/decline to "the other party."
    requested_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status: Mapped[FamilyLinkStatus] = mapped_column(
        Enum(FamilyLinkStatus, name="familylinkstatus"), nullable=False, default=FamilyLinkStatus.pending
    )
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # At most one row per ordered (guardian, child) pair, ever — decline
    # and unlink both delete the row rather than persisting a terminal
    # state, so this covers "duplicate pending request" and "pending
    # while already accepted" with a single constraint.
    __table_args__ = (UniqueConstraint("guardian_id", "child_id", name="uq_family_links_guardian_child"),)
