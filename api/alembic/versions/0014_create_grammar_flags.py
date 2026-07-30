"""create grammar_flags table

Revision ID: 0014
Revises: 0013
Create Date: 2026-07-30

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0014"
down_revision: Union[str, None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "grammar_flags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content.id"), nullable=False),
        sa.Column("concept_id", sa.String(length=50), nullable=False),
        sa.Column("sentence", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "self_corrected", "kept_as_is", name="grammarflagstatus"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("content_id", "concept_id", "sentence", name="uq_grammar_flags_content_concept_sentence"),
    )
    op.create_index(
        "ix_grammar_flags_content_status",
        "grammar_flags",
        ["content_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_grammar_flags_content_status", table_name="grammar_flags")
    op.drop_table("grammar_flags")
    sa.Enum(name="grammarflagstatus").drop(op.get_bind(), checkfirst=True)
