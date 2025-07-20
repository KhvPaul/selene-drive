from unittest import mock  # noqa

import pytest

from httpx import AsyncClient
import sqlalchemy as sa
from sqlalchemy.orm import scoped_session, sessionmaker  # noqa

pytestmark = pytest.mark.asyncio


async def some_async_func(a: int, b: int):
    return a + b


async def test_some_asyncio_code(session_cls, client: AsyncClient):
    async with session_cls() as session:
        await session.execute(sa.text("SELECT 1"))
    res = await some_async_func(3, 7)
    assert res == 10
    resp = await client.get("/docs")
    assert resp.is_success
