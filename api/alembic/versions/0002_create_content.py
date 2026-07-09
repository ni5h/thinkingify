"""create content table

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "content",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.String(length=500), nullable=True),
        sa.Column("content_markdown", sa.Text(), nullable=False, server_default=""),
        sa.Column("feature_image_url", sa.String(length=1024), nullable=True),
        sa.Column(
            "status",
            sa.Enum("draft", "pending_review", "published", "archived", name="contentstatus"),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_content_slug", "content", ["slug"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_content_slug", table_name="content")
    op.drop_table("content")
    sa.Enum(name="contentstatus").drop(op.get_bind(), checkfirst=True)
