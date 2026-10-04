from datetime import UTC, datetime

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    # All Thinkingify tables live in a dedicated `thinkingify` Postgres schema
    # so the app can share one database with other projects (e.g. sweet_pills,
    # which lives in its own `sweetpills` schema) without name collisions. This
    # fully-qualifies every table and every runtime query as `thinkingify.*`.
    metadata = MetaData(schema="thinkingify")


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
