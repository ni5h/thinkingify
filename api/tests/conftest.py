import os
import uuid
from collections.abc import AsyncGenerator

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id")
os.environ.setdefault("JWT_SECRET", "test-secret")

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.models import Base
from app.models.user import User, UserRole

# sqlite in-memory, not Alembic migrations — fast, and content_service tests
# only exercise business logic, not migration history. Real Postgres/Supabase
# is verified separately via `alembic upgrade head` (see api/README.md).
_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:", poolclass=StaticPool, connect_args={"check_same_thread": False}
)
_SessionLocal = async_sessionmaker(_engine, expire_on_commit=False)


# Models now live in a `thinkingify` schema (MetaData(schema="thinkingify")).
# Postgres has that schema; SQLite models a "schema" as an attached database,
# so attach an in-memory one named `thinkingify` on connect — otherwise
# create_all/queries fail with "unknown database thinkingify". StaticPool keeps
# a single connection, so this runs once and persists across tests.
@event.listens_for(_engine.sync_engine, "connect")
def _attach_thinkingify_schema(dbapi_connection, _connection_record):
    dbapi_connection.execute("ATTACH DATABASE ':memory:' AS thinkingify")


@pytest.fixture(autouse=True)
async def _reset_schema() -> AsyncGenerator[None, None]:
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with _SessionLocal() as session:
        yield session


@pytest.fixture
def app():
    from app.main import app as fastapi_app

    async def override_get_db():
        async with _SessionLocal() as session:
            yield session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    yield fastapi_app
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def client(app):
    from fastapi.testclient import TestClient

    return TestClient(app)


@pytest.fixture
async def admin_user(db: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        google_sub="google-admin",
        email="admin@example.com",
        name="Admin",
        role=UserRole.admin,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def author_user(db: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        google_sub="google-author",
        email="author@example.com",
        name="Author",
        role=UserRole.author,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def learner_user(db: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        google_sub="google-learner",
        email="learner@example.com",
        name="Learner",
        role=UserRole.learner,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
