"""add profile fields to users

Revision ID: 0011
Revises: 0010
Create Date: 2026-07-26

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Unlike op.create_table (which auto-creates an Enum type it encounters),
    # op.add_column does not — the type must be created explicitly first.
    account_type_enum = sa.Enum("parent", "child", name="accounttype")
    account_type_enum.create(op.get_bind(), checkfirst=True)
    op.add_column("users", sa.Column("account_type", account_type_enum, nullable=True))
    op.add_column("users", sa.Column("first_name", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("last_name", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("username", sa.String(30), nullable=True))
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.add_column("users", sa.Column("tagline", sa.String(140), nullable=True))
    op.add_column("users", sa.Column("school_name", sa.String(150), nullable=True))
    op.add_column("users", sa.Column("occupation", sa.String(150), nullable=True))
    op.add_column("users", sa.Column("location_city", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("location_state", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("location_country", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "location_country")
    op.drop_column("users", "location_state")
    op.drop_column("users", "location_city")
    op.drop_column("users", "occupation")
    op.drop_column("users", "school_name")
    op.drop_column("users", "tagline")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_column("users", "username")
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
    op.drop_column("users", "account_type")
    sa.Enum(name="accounttype").drop(op.get_bind(), checkfirst=True)
