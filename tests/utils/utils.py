import contextlib
import httpx
from functools import wraps

from fastapi import FastAPI


registered_functions = []


@contextlib.asynccontextmanager
async def async_test_client(
    app: FastAPI | None = None,
    base_url: str = "http://localhost",
) -> httpx.AsyncClient | None:
    if not app:
        from main import app as current_app
        app = current_app
    async with httpx.AsyncClient(app=app, base_url=base_url) as async_con:
        yield async_con

def async_calls_counter(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        wrapper.call_count += 1
        return await func(*args, **kwargs)

    wrapper.call_count = 0
    registered_functions.append(wrapper)
    return wrapper


def sync_calls_counter(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        wrapper.call_count += 1
        return func(*args, **kwargs)

    wrapper.call_count = 0
    registered_functions.append(wrapper)
    return wrapper
