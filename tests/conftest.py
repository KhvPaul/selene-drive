import asyncio
import contextlib
import typing as t

import pytest
import pytest_asyncio
import uvloop
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, future

from main import app
from utils.annotations import get_async_db_session

from .utils import db as db_helper

pytestmark = pytest.mark.asyncio(loop_scope="session")
TEST_SKIP_CLEANUP_TABLES = []


@pytest.fixture(scope="session")
def event_loop(request):
    loop = uvloop.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture(name="_session_cls", scope="session")
async def connection(event_loop):
    async with db_helper.test_database_session() as session_cls:
        app.dependency_overrides[get_async_db_session] = lambda: session_cls
        yield session_cls


@pytest_asyncio.fixture(name="session_cls")
async def clean_up_db(_session_cls):
    # testing cleaning up db after each test
    async with _session_cls() as session:
        for model_cls in db_helper.models_cls_generator():
            if "view" in model_cls.name:
                # ignore POSTGRES VIEW tables
                continue
            smtp = delete(model_cls)
            await session.execute(smtp)
            await session.commit()
        for model_cls in db_helper.models_cls_generator():
            smtp = future.select(model_cls)
            res = await session.execute(smtp)
            assert not res.scalars().all()
    # await populate_database.populate(_session_cls)
    yield _session_cls


@contextlib.asynccontextmanager
async def async_test_client(app: FastAPI, base_url: str = "http://test") -> t.AsyncGenerator[AsyncClient]:
    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url=base_url) as client:
        yield client


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    async with async_test_client(app) as client:
        yield client
