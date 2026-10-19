"""card-session + pipeline fields on assets and items

Revision ID: 0022
Revises: 0021
Create Date: 2026-10-19

Adds the offline content-pipeline (Phase 2) fields: card/recap asset kinds,
ordered structured card payloads, multiple-choice check questions with a hint
and a source card, and the dedupe score written back onto generated content.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0022"
down_revision: Union[str, None] = "0021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # New asset kinds. ADD VALUE is transaction-safe on PG12+ as long as the new
    # value isn't used in the same transaction (we only add columns here).
    op.execute("ALTER TYPE thinkingify.assetkind ADD VALUE IF NOT EXISTS 'card'")
    op.execute("ALTER TYPE thinkingify.assetkind ADD VALUE IF NOT EXISTS 'recap'")

    op.add_column("assets", sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("assets", sa.Column("data", sa.JSON(), nullable=True))
    op.add_column("assets", sa.Column("dedupe_score", sa.Float(), nullable=True))

    op.add_column("items", sa.Column("options", sa.JSON(), nullable=True))
    op.add_column("items", sa.Column("hint", sa.Text(), nullable=True))
    op.add_column("items", sa.Column("source_asset_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("items", sa.Column("dedupe_score", sa.Float(), nullable=True))
    op.create_foreign_key(
        "fk_items_source_asset", "items", "assets", ["source_asset_id"], ["id"]
    )


def downgrade() -> None:
    op.drop_constraint("fk_items_source_asset", "items", type_="foreignkey")
    op.drop_column("items", "dedupe_score")
    op.drop_column("items", "source_asset_id")
    op.drop_column("items", "hint")
    op.drop_column("items", "options")
    op.drop_column("assets", "dedupe_score")
    op.drop_column("assets", "data")
    op.drop_column("assets", "order_index")
    # Postgres has no DROP VALUE; the added enum labels (card, recap) are left in
    # place on downgrade. Harmless — nothing references them once columns go.
