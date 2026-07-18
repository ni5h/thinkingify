"""add topic_id and style to content

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-18

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "content",
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topics.id"), nullable=True),
    )
    op.add_column("content", sa.Column("style", sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column("content", "style")
    op.drop_column("content", "topic_id")
