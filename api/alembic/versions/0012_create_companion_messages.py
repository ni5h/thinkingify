"""create companion_messages table

Revision ID: 0012
Revises: 0011
Create Date: 2026-07-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "companion_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.Enum("user", "assistant", name="companionmessagerole"), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("ladder_level", sa.Integer(), nullable=True),
        sa.Column("direct_answer_requested", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("fact_leak_blocked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_fallback", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_companion_messages_content_user_created",
        "companion_messages",
        ["content_id", "user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_companion_messages_content_user_created", table_name="companion_messages")
    op.drop_table("companion_messages")
    sa.Enum(name="companionmessagerole").drop(op.get_bind(), checkfirst=True)
