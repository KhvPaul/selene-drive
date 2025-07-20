import contextlib
import os
import uuid

import asyncpg
from alembic import command
from alembic import config
from sqlalchemy.ext import asyncio as sa_asyncio
from testcontainers import postgres

from db import models
from config import settings
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
    migrations: list[str],
    migrations_folder_name: str = "migrations",
):
    """
    Apply specific migration
    :param pgsql_endpoint: PostgreSQL endpoint
    :param migrations: migration revision id
    :param migrations_folder_name: migrations folder name
    :return:
    """
    alembic_cfg = config.Config(os.path.join(settings.BASE_DIR, "alembic.ini"))
    alembic_cfg.set_main_option("script_location", os.path.join(settings.BASE_DIR, "db", migrations_folder_name))
    alembic_cfg.set_main_option("sqlalchemy.url", pgsql_endpoint)
    base_versions_path = os.path.join(settings.BASE_DIR, "db", migrations_folder_name, "versions")
    version_subdirs = [
        base_versions_path,
        os.path.join(base_versions_path, "create"),
        os.path.join(base_versions_path, "drop"),
        os.path.join(base_versions_path, "insert"),
        os.path.join(base_versions_path, "update"),
        os.path.join(base_versions_path, "triggers"),
    ]
    alembic_cfg.set_main_option("version_locations", os.pathsep.join(version_subdirs))
    # versions_folders = os.listdir(versions_dir)
    # versions_folders = [
    #     os.path.join(versions_dir, el) for el in versions_folders if os.path.isdir(os.path.join(versions_dir, el))
    # ]
    for migration_version in migrations:
        command.upgrade(alembic_cfg, migration_version)


@contextlib.asynccontextmanager
async def _database_session_local(
    skip_migrations=False,
) -> sa_asyncio.AsyncSession:
    from db import session as session_api

    with postgres.PostgresContainer("postgres:17.5-alpine") as pgsql_container:
        sync_pgsql_connection_url = test_helpers.fix_sqlalchemy_url(pgsql_container.get_connection_url(), sync=True)
        async_pgsql_connection_url = test_helpers.fix_sqlalchemy_url(pgsql_container.get_connection_url(), sync=False)
        if not skip_migrations:
            apply_specific_migration(
                pgsql_endpoint=sync_pgsql_connection_url,
                migrations=["98f8bb68cc11", "head"],
            )

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
    from db import session as session_api

    database = uuid.uuid4().hex
    await __recreate_database(database)
    print(database)  # noqa T201
    if not skip_migrations:
        apply_specific_migration(pgsql_endpoint=str(settings.DATABASE_ENDPOINT), migrations=["5fad8c5669e9", "head"])

    async_engine = session_api.create_async_engine(endpoint=str(settings.ASYNC_DATABASE_ENDPOINT))
    sync_engine = session_api.create_sync_engine(endpoint=str(settings.DATABASE_ENDPOINT))
    async with session_api.get_async_postgres_session(async_engine) as session_cls:
        setattr(session_cls, "sync_engine", sync_engine)
        yield session_cls


test_database_session = _database_session_in_ci if os.getenv("IN_CI", False) else _database_session_local
