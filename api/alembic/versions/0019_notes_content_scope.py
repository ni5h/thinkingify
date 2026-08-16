"""allow content-scoped notes (blank posts)

Revision ID: 0019
Revises: 0018
Create Date: 2026-08-16

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0019"
down_revision: Union[str, None] = "0018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("notes", "topic_id", existing_type=postgresql.UUID(as_uuid=True), nullable=True)
    op.add_column(
        "notes",
        sa.Column("content_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content.id"), nullable=True),
    )
    op.create_unique_constraint("uq_notes_content_user", "notes", ["content_id", "user_id"])


def downgrade() -> None:
    op.drop_constraint("uq_notes_content_user", "notes", type_="unique")
    op.drop_column("notes", "content_id")
    op.alter_column("notes", "topic_id", existing_type=postgresql.UUID(as_uuid=True), nullable=False)
