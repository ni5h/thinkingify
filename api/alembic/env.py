import asyncio
import uuid
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool, text
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings
from app.models import Base  # noqa: F401 — ensures all models are registered

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

SCHEMA = "thinkingify"


def include_name(name, type_, parent_names):
    # include_schemas=True makes autogenerate reflect every schema in the
    # database, including Supabase's own auth/storage/realtime/vault system
    # schemas and any other app's schema (e.g. sweetpills) — none of which are
    # in target_metadata. Without this filter, autogenerate would propose
    # dropping all of them.
    if type_ == "schema":
        return name in (None, SCHEMA)
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema=SCHEMA,
        include_schemas=True,
        include_name=include_name,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table_schema=SCHEMA,
        include_schemas=True,
        include_name=include_name,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args={
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
            "prepared_statement_name_func": lambda: f"__asyncpg_{uuid.uuid4()}__",
            # Land every object in the `thinkingify` schema: the 0001–0020
            # migrations use unqualified op.create_table calls, and Alembic's
            # own version table lives in this schema too. Setting search_path at
            # connect time (not with an in-transaction SET, which broke Alembic's
            # transaction commit) means it's active before any DDL. `public`
            # stays on the path so shared extensions resolve. Runtime doesn't
            # depend on this — MetaData(schema=...) fully-qualifies queries.
            "server_settings": {"search_path": f"{SCHEMA}, public"},
        },
    )
    # Create the schema in its own committed transaction first — Alembic creates
    # its version table (thinkingify.alembic_version) before running any
    # migration, so the schema must already exist.
    async with connectable.connect() as connection:
        await connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"))
        await connection.commit()
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
