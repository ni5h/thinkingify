"""create spelling_flags table

Revision ID: 0013
Revises: 0012
Create Date: 2026-07-29

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "spelling_flags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content.id"), nullable=False),
        sa.Column("word", sa.String(length=100), nullable=False),
        sa.Column(
            "error_type", sa.Enum("misspelling", "homophone", name="spellingerrortype"), nullable=False
        ),
        sa.Column("context_sentence", sa.Text(), nullable=False),
        sa.Column("suggested_correction", sa.Text(), nullable=True),
        sa.Column("hint", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "self_corrected", "kept_as_is", name="spellingflagstatus"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("hint_revealed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("content_id", "word", name="uq_spelling_flags_content_word"),
    )
    op.create_index(
        "ix_spelling_flags_content_status",
        "spelling_flags",
        ["content_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_spelling_flags_content_status", table_name="spelling_flags")
    op.drop_table("spelling_flags")
    sa.Enum(name="spellingflagstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="spellingerrortype").drop(op.get_bind(), checkfirst=True)
