import contextlib

from sqlalchemy import create_engine
from sqlalchemy.ext import asyncio as sa_asyncio
from sqlalchemy.future import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool, QueuePool

from config import settings


def create_async_engine(
    echo: bool = settings.ECHO_QUERY, endpoint=str(settings.ASYNC_DATABASE_ENDPOINT)
) -> sa_asyncio.AsyncEngine:
    return sa_asyncio.create_async_engine(
        endpoint,
        poolclass=AsyncAdaptedQueuePool,
        echo=echo,
        pool_size=int(settings.DATABASE_MAX_CONNECTIONS) * 0.9,
        max_overflow=int(settings.DATABASE_MAX_CONNECTIONS) * 0.1,
        pool_recycle=-1,
        pool_timeout=30,
        echo_pool=True,
        future=True,
        pool_pre_ping=True,
    )


def create_sync_engine(echo: bool = settings.ECHO_QUERY, endpoint=str(settings.DATABASE_ENDPOINT)) -> Engine:
    return create_engine(
        endpoint,
        poolclass=QueuePool,
        echo=echo,
        pool_size=int(settings.DATABASE_MAX_CONNECTIONS) * 0.9,
        max_overflow=int(settings.DATABASE_MAX_CONNECTIONS) * 0.1,
        pool_recycle=-1,
        pool_timeout=30,
        echo_pool=True,
        future=True,
        pool_pre_ping=True,
    )


_async_engine = create_async_engine()


@contextlib.asynccontextmanager
async def get_async_postgres_session(engine: sa_asyncio.AsyncEngine = _async_engine) -> sessionmaker:
    async_session_cls = sessionmaker(bind=engine, class_=sa_asyncio.AsyncSession, expire_on_commit=True)
    yield async_session_cls


@contextlib.asynccontextmanager
async def get_sync_postgres_session(engine: Engine | None = None) -> sessionmaker:
    engine = engine or create_sync_engine()
    session_cls = sessionmaker(bind=engine, expire_on_commit=True)
    yield session_cls
