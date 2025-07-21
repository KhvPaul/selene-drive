from typing import Annotated

from fastapi import Depends
from sqlalchemy import orm as so
from sqlalchemy.ext import asyncio as sa_asyncio

from db.session import get_async_postgres_session, get_sync_postgres_session


def get_db() -> so.Session:
    with get_sync_postgres_session() as db:
        yield db


async def get_async_db_session() -> so.sessionmaker[sa_asyncio.AsyncSession]:
    async with get_async_postgres_session() as session_cls:
        yield session_cls


Session = Annotated[so.Session, Depends(get_db)]
AsyncSession = Annotated[sa_asyncio.AsyncSession, Depends(get_async_db_session)]
