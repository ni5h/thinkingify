"""create math room tables

Revision ID: 0017
Revises: 0016
Create Date: 2026-08-09

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0017"
down_revision: Union[str, None] = "0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "math_problems",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("statement_markdown", sa.Text(), nullable=False),
        sa.Column("answer", sa.String(length=255), nullable=False),
        sa.Column("answer_kind", sa.Enum("integer", "text", name="mathanswerkind"), nullable=False),
        sa.Column("solution_markdown", sa.Text(), nullable=False),
        sa.Column("concept_tags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("difficulty", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "status",
            sa.Enum("draft", "published", name="mathproblemstatus"),
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
    op.create_index("ix_math_problems_slug", "math_problems", ["slug"], unique=True)

    op.create_table(
        "math_coach_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "math_problem_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("math_problems.id"), nullable=False
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.Enum("user", "assistant", name="mathcoachmessagerole"), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("ladder_level", sa.Integer(), nullable=True),
        sa.Column("asked_for_answer", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("answer_leak_blocked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_fallback", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_math_coach_messages_problem_user_created",
        "math_coach_messages",
        ["math_problem_id", "user_id", "created_at"],
    )

    op.create_table(
        "math_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "math_problem_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("math_problems.id"), nullable=False
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("submitted_answer", sa.String(length=255), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_math_attempts_problem_user_created", "math_attempts", ["math_problem_id", "user_id", "created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_math_attempts_problem_user_created", table_name="math_attempts")
    op.drop_table("math_attempts")
    op.drop_index("ix_math_coach_messages_problem_user_created", table_name="math_coach_messages")
    op.drop_table("math_coach_messages")
    op.drop_index("ix_math_problems_slug", table_name="math_problems")
    op.drop_table("math_problems")
    sa.Enum(name="mathcoachmessagerole").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="mathproblemstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="mathanswerkind").drop(op.get_bind(), checkfirst=True)
