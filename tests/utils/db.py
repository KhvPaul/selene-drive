import contextlib
import os
import uuid

import asyncpg
from alembic import command, config
from sqlalchemy.ext import asyncio as sa_asyncio
from testcontainers import postgres

from config import settings
from db import models
from db import session as session_api

from ..utils import helpers as test_helpers


def models_cls_generator():
    metadata = models.Base.metadata
    models_ = list(metadata.sorted_tables)
    models_.reverse()
    for model in models_:  # noqa: UP028
        yield model


async def __recreate_database(database: str, connection_url: str | None = None):
    if connection_url:
        sys_conn = await asyncpg.connect(dsn=connection_url)
    else:
        sys_conn = await asyncpg.connect(
            host=settings.POSTGRES_HOST,
            database=settings.POSTGRES_DB,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            port=settings.POSTGRES_PORT,
        )
    try:
        await sys_conn.execute(f'DROP DATABASE "{database}";')
    except Exception:
        # it may appear that DB does not exist for now,
        # so let's just skip the failure
        pass

    await sys_conn.execute(f'CREATE DATABASE "{database}";')
    print("database cleaned-up!")  # noqa T201

    await sys_conn.close()


def apply_specific_migration(
    pgsql_endpoint: str,
    migration: str = "head",
):
    """
    Apply specific migration
    :param pgsql_endpoint: PostgreSQL endpoint
    :param migration: migration revision id
    :return:
    """
    alembic_cfg = config.Config(os.path.join(settings.BASE_DIR, "alembic.ini"))
    alembic_cfg.set_main_option("script_location", os.path.join(settings.BASE_DIR, "db", "migrations"))
    alembic_cfg.set_main_option("sqlalchemy.url", pgsql_endpoint)
    versions_dir = os.path.join(settings.BASE_DIR, "db", "migrations", "versions")
    versions_folders = os.listdir(versions_dir)
    versions_folders = [
        os.path.join(versions_dir, el) for el in versions_folders if os.path.isdir(os.path.join(versions_dir, el))
    ]
    versions_folders_s = " ".join(versions_folders)
    alembic_cfg.set_main_option("version_locations", versions_folders_s)
    command.upgrade(alembic_cfg, migration)


@contextlib.asynccontextmanager
async def _database_session_local(
    skip_migrations=False,
) -> sa_asyncio.AsyncSession:
    with postgres.PostgresContainer("postgres:17.5-alpine") as pgsql_container:
        sync_pgsql_connection_url = test_helpers.fix_sqlalchemy_url(pgsql_container.get_connection_url(), sync=True)
        async_pgsql_connection_url = test_helpers.fix_sqlalchemy_url(pgsql_container.get_connection_url(), sync=False)
        if not skip_migrations:
            apply_specific_migration(sync_pgsql_connection_url)

        async_engine = session_api.create_async_engine(endpoint=async_pgsql_connection_url)
        sync_engine = session_api.create_sync_engine(endpoint=sync_pgsql_connection_url)
        async with session_api.get_async_postgres_session(async_engine) as session_cls:
            psql_conn_url = str(session_cls.kw["bind"].engine.url)
            psql_conn_url = psql_conn_url.replace("***", "test").replace("postgresql+asyncpg", "postgres")
            psql_conn_url = "psql " + psql_conn_url
            setattr(session_cls, "_psql_conn_url", psql_conn_url)
            setattr(session_cls, "sync_engine", sync_engine)
            yield session_cls


@contextlib.asynccontextmanager
async def _database_session_in_ci(skip_migrations=False) -> sa_asyncio.AsyncSession:
    database = uuid.uuid4().hex
    await __recreate_database(database)
    print(database)  # noqa T201
    if not skip_migrations:
        apply_specific_migration(str(settings.DATABASE_ENDPOINT), "head")

    async_engine = session_api.create_async_engine(endpoint=str(settings.ASYNC_DATABASE_ENDPOINT))
    sync_engine = session_api.create_sync_engine(endpoint=str(settings.DATABASE_ENDPOINT))
    async with session_api.get_async_postgres_session(async_engine) as session_cls:
        setattr(session_cls, "sync_engine", sync_engine)
        yield session_cls


test_database_session = _database_session_in_ci if settings.IN_CI else _database_session_local
