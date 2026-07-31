"""create parent_reports table

Revision ID: 0016
Revises: 0015
Create Date: 2026-07-31

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0016"
down_revision: Union[str, None] = "0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "parent_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content.id"), nullable=False),
        sa.Column("word_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("headline", sa.Text(), nullable=False),
        sa.Column("creativity_narrative", sa.Text(), nullable=False),
        sa.Column("suggested_action", sa.Text(), nullable=True),
        sa.Column("went_well", sa.JSON(), nullable=False),
        sa.Column("was_tricky", sa.JSON(), nullable=False),
        sa.Column("stage_breakdown", sa.JSON(), nullable=False),
        sa.Column("ai_help_level", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_parent_reports_content_created", "parent_reports", ["content_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_parent_reports_content_created", table_name="parent_reports")
    op.drop_table("parent_reports")
