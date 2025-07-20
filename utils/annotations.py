from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy.ext import asyncio as sa_asyncio

from db.session import get_sync_postgres_session, get_async_postgres_session


def get_db() -> Session:
    with get_sync_postgres_session() as db:
        yield db


async def get_async_db_session() -> sa_asyncio.AsyncSession:
    async with get_async_postgres_session() as session_cls:
        yield session_cls


Session = Annotated[Session, Depends(get_db)]
AsyncSession = Annotated[sa_asyncio.AsyncSession, Depends(get_async_db_session)]
