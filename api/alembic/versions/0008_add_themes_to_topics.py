"""add themes to topics

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "topics",
        sa.Column(
            "themes",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
    )


def downgrade() -> None:
    op.drop_column("topics", "themes")
