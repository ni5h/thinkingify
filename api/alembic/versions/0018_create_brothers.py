"""create brothers fluency-module tables

Revision ID: 0018
Revises: 0017
Create Date: 2026-08-15

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0018"
down_revision: Union[str, None] = "0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "brother_tier_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("tier_id", sa.String(length=10), nullable=False),
        sa.Column(
            "status",
            sa.Enum("locked", "active", "mastered", name="brothertierstatus"),
            nullable=False,
            server_default="locked",
        ),
        sa.Column("baseline_ms", sa.Integer(), nullable=True),
        sa.Column("mastered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "tier_id", name="uq_brother_tier_progress_user_tier"),
    )

    op.create_table(
        "brother_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("tier_id", sa.String(length=10), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("correct_answer", sa.Integer(), nullable=False),
        sa.Column("user_answer", sa.Integer(), nullable=False),
        sa.Column("correct", sa.Boolean(), nullable=False),
        sa.Column("response_ms", sa.Integer(), nullable=False),
        sa.Column("is_retention", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_preview", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_brother_attempts_user_tier_created", "brother_attempts", ["user_id", "tier_id", "created_at"]
    )

    op.create_table(
        "brother_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("questions", sa.JSON(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("active", "complete", name="brothersessionstatus"),
            nullable=False,
            server_default="active",
        ),
        sa.Column("answered_indexes", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_brother_sessions_user_created", "brother_sessions", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_brother_sessions_user_created", table_name="brother_sessions")
    op.drop_table("brother_sessions")
    op.drop_index("ix_brother_attempts_user_tier_created", table_name="brother_attempts")
    op.drop_table("brother_attempts")
    op.drop_table("brother_tier_progress")
    sa.Enum(name="brothersessionstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="brothertierstatus").drop(op.get_bind(), checkfirst=True)
