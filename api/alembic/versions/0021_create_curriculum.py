"""create concept-map (curriculum) tables

Revision ID: 0021
Revises: 0020
Create Date: 2026-10-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0021"
down_revision: Union[str, None] = "0020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create all enum types explicitly up front (checkfirst) and reference them
    # with create_type=False on every column — curriculumstatus is shared by two
    # tables, so letting create_table auto-create would try to CREATE TYPE twice.
    bind = op.get_bind()
    status_col = postgresql.ENUM("draft", "reviewed", "live", "retired", name="curriculumstatus", create_type=False)
    asset_kind = postgresql.ENUM("audio", "script", "visual", name="assetkind", create_type=False)
    item_kind = postgresql.ENUM(
        "recall", "apply", "explain", "spot_the_mistake", "puzzle", name="itemkind", create_type=False
    )
    writing_kind = postgresql.ENUM("explain", "recall", name="writingkind", create_type=False)
    for enum_type in (status_col, asset_kind, item_kind, writing_kind):
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "subjects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("grade", sa.Integer(), nullable=False, server_default="4"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_subjects_code", "subjects", ["code"], unique=True)

    op.create_table(
        "chapters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subjects.id"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("book_refs", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "concepts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("chapter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chapters.id"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("prerequisites", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subjects.id"), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("concept_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("concepts.id"), nullable=False),
        sa.Column("kind", asset_kind, nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("url", sa.String(length=1024), nullable=True),
        sa.Column("status", status_col, nullable=False, server_default="draft"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("concept_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("concepts.id"), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skills.id"), nullable=True),
        sa.Column("kind", item_kind, nullable=False),
        sa.Column("difficulty", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("body", sa.Text(), nullable=False, server_default=""),
        sa.Column("answer_key", sa.Text(), nullable=True),
        sa.Column("status", status_col, nullable=False, server_default="draft"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_items_concept", "items", ["concept_id"])

    op.create_table(
        "book_maps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("book", sa.String(length=255), nullable=False),
        sa.Column("chapter_ref", sa.String(length=100), nullable=False),
        sa.Column("concept_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "mastery",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("child_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("concept_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("concepts.id"), nullable=False),
        sa.Column("baseline", sa.Integer(), nullable=True),
        sa.Column("state", sa.String(length=30), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("child_id", "concept_id", name="uq_mastery_child_concept"),
    )

    op.create_table(
        "writing",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("child_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("concept_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("concepts.id"), nullable=False),
        sa.Column("kind", writing_kind, nullable=False),
        sa.Column("text", sa.Text(), nullable=False, server_default=""),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("writing")
    op.drop_table("mastery")
    op.drop_table("book_maps")
    op.drop_index("ix_items_concept", table_name="items")
    op.drop_table("items")
    op.drop_table("assets")
    op.drop_table("skills")
    op.drop_table("concepts")
    op.drop_table("chapters")
    op.drop_index("ix_subjects_code", table_name="subjects")
    op.drop_table("subjects")
    sa.Enum(name="writingkind").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="itemkind").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="assetkind").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="curriculumstatus").drop(op.get_bind(), checkfirst=True)
