"""create sentence_framing_flags table

Revision ID: 0015
Revises: 0014
Create Date: 2026-07-30

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0015"
down_revision: Union[str, None] = "0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sentence_framing_flags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content.id"), nullable=False),
        sa.Column("concept_id", sa.String(length=50), nullable=False),
        sa.Column("sentences", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "self_corrected", "kept_as_is", name="sentenceframingflagstatus"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "content_id", "concept_id", "sentences", name="uq_sentence_framing_flags_content_concept_sentences"
        ),
    )
    op.create_index(
        "ix_sentence_framing_flags_content_status",
        "sentence_framing_flags",
        ["content_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_sentence_framing_flags_content_status", table_name="sentence_framing_flags")
    op.drop_table("sentence_framing_flags")
    sa.Enum(name="sentenceframingflagstatus").drop(op.get_bind(), checkfirst=True)
