"""add audio_transcript to topics

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-25

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("topics", sa.Column("audio_transcript", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("topics", "audio_transcript")
