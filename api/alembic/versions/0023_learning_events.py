"""answer events, practice sessions, concept mastered_at (Phase 3)

Revision ID: 0023
Revises: 0022
Create Date: 2026-10-19
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0023"
down_revision: Union[str, None] = "0022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    answer_result = postgresql.ENUM("right", "wrong", "unsure", name="answerresult", create_type=False)
    answer_result.create(bind, checkfirst=True)

    op.add_column("mastery", sa.Column("mastered_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "answer_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("child_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("items.id"), nullable=False),
        sa.Column("concept_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("concepts.id"), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("result", answer_result, nullable=False),
        sa.Column("hint_used", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_answer_events_child_concept", "answer_events", ["child_id", "concept_id"])

    op.create_table(
        "practice_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("child_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("concept_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("concepts.id"), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False, server_default="check"),
        sa.Column("level", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("start_level", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("up_streak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("miss_streak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("asked_item_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("answered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("right_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("practice_sessions")
    op.drop_index("ix_answer_events_child_concept", table_name="answer_events")
    op.drop_table("answer_events")
    op.drop_column("mastery", "mastered_at")
    sa.Enum(name="answerresult").drop(op.get_bind(), checkfirst=True)
