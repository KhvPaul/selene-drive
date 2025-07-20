import asyncio
import contextlib
import typing as t

import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import delete, future
from httpx import AsyncClient, ASGITransport

from utils.annotations import get_async_db_session
from .utils import utils as test_utils, db as db_helper


from main import app

pytestmark = pytest.mark.asyncio
TEST_SKIP_CLEANUP_TABLES = []


@pytest.fixture(scope="session")
def event_loop(request):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture(name="_session_cls", scope="session")
async def connection(event_loop):
    async with db_helper.test_database_session() as session_cls:
        app.dependency_overrides[get_async_db_session] = lambda: session_cls
        # user this for set up default user for authorisation
        # app.dependency_overrides[get_sub_checker] = lambda: constants.DEFAULT_USER_ID
        yield session_cls


@pytest_asyncio.fixture(name="session_cls")
async def clean_up_db(_session_cls):
    # testing cleaning up db after each test
    async with _session_cls() as session:
        for model_cls in db_helper.models_cls_generator():
            if "view" in model_cls.name:
                # ignore POSTGRES VIEW tables
                continue
            if model_cls.name in TEST_SKIP_CLEANUP_TABLES:
                continue
            smtp = delete(model_cls)
            await session.execute(smtp)
            await session.commit()
        for model_cls in db_helper.models_cls_generator():
            if model_cls.name in TEST_SKIP_CLEANUP_TABLES:
                continue
            smtp = future.select(model_cls)
            res = await session.execute(smtp)
            assert not res.scalars().all()
    # await populate_database.populate(_session_cls)
    yield _session_cls



@contextlib.asynccontextmanager
async def async_test_client(app: FastAPI, base_url: str = "http://test") -> t.AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url=base_url) as client:
        yield client


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    async with async_test_client(app) as client:
        yield client
