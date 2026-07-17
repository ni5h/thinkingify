"""add learner role to userrole enum

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-17

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Postgres forbids using a newly-added enum value in the same
    # transaction it was added in, so this stays its own migration rather
    # than being merged into the migration that creates tables using it.
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'learner'")


def downgrade() -> None:
    # Postgres has no clean way to remove a single enum value (would require
    # rebuilding the type and every column/table using it). Not supported.
    raise NotImplementedError("Cannot downgrade: removing a value from the userrole enum is not supported.")
