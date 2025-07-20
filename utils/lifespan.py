from contextlib import asynccontextmanager

from fastapi import FastAPI

from config import settings
from db.session import get_async_postgres_session
from logger import logger
from managers import RoverManager



@asynccontextmanager
async def lifespan(app: FastAPI):
    async with get_async_postgres_session() as session_cls:
        if not await RoverManager.check_rover_already_landed(session_cls=session_cls):
            await RoverManager.initialize_rover(
                session_cls=session_cls,
                longitude=settings.START_POSTITION[0],
                latitude=settings.START_POSTITION[1],
                direction=settings.START_DIRECTION,
            )
            logger.info(
                f"Rover successfully landed."
                f"Coord ({settings.ROVER_INITIAL_LONGITUDE}, {settings.ROVER_INITIAL_LATITUDE})"
            )
    yield
