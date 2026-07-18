"""create topics table

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-18

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "topics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("explainer_markdown", sa.Text(), nullable=False, server_default=""),
        sa.Column("audio_url", sa.String(length=1024), nullable=True),
        sa.Column(
            "status",
            sa.Enum("draft", "published", name="topicstatus"),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_topics_slug", "topics", ["slug"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_topics_slug", table_name="topics")
    op.drop_table("topics")
    sa.Enum(name="topicstatus").drop(op.get_bind(), checkfirst=True)
