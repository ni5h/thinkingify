"""create puzzle_game_progress and puzzle_attempts tables

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# create_type=False: this enum is referenced in 4 columns across 2 tables in
# this one migration. Without create_type=False, SQLAlchemy attempts to
# create the type again as a side effect of each op.create_table() call
# (checkfirst on the explicit .create() below doesn't prevent that implicit
# re-creation) — this is the standard Alembic pattern for an enum shared
# across multiple tables in a single migration.
PUZZLE_TIER_ENUM = postgresql.ENUM(
    "trial", "beginner", "intermediate", "advanced", "pro", name="puzzletier", create_type=False
)


def upgrade() -> None:
    PUZZLE_TIER_ENUM.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "puzzle_game_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("game_id", sa.String(length=50), nullable=False),
        sa.Column("current_tier", PUZZLE_TIER_ENUM, nullable=False, server_default="trial"),
        sa.Column("variations_completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("highest_tier_unlocked", PUZZLE_TIER_ENUM, nullable=False, server_default="trial"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "game_id", name="uq_puzzle_game_progress_user_game"),
    )

    op.create_table(
        "puzzle_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("game_id", sa.String(length=50), nullable=False),
        sa.Column("tier", PUZZLE_TIER_ENUM, nullable=False),
        sa.Column("variation_index", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("time_taken_ms", sa.Integer(), nullable=False),
        sa.Column("correct", sa.Boolean(), nullable=False),
        sa.Column("beat_time_limit", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_puzzle_attempts_user_id", "puzzle_attempts", ["user_id"])
    op.create_index("ix_puzzle_attempts_game_id", "puzzle_attempts", ["game_id"])
    op.create_index(
        "ix_puzzle_attempts_user_game_created",
        "puzzle_attempts",
        ["user_id", "game_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_puzzle_attempts_user_game_created", table_name="puzzle_attempts")
    op.drop_index("ix_puzzle_attempts_game_id", table_name="puzzle_attempts")
    op.drop_index("ix_puzzle_attempts_user_id", table_name="puzzle_attempts")
    op.drop_table("puzzle_attempts")
    op.drop_table("puzzle_game_progress")
    PUZZLE_TIER_ENUM.drop(op.get_bind(), checkfirst=True)
