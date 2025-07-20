from contextlib import asynccontextmanager

from fastapi import FastAPI

from config import settings
from db.session import get_async_postgres_session
from logger import logger
from managers import RoverManager
from utils import exceptions as custom_exc



@asynccontextmanager
async def lifespan(app: FastAPI):
    async with get_async_postgres_session() as session_cls:
        # initialize obstacles if exists predefined
        if settings.INITIAL_OBSTACLES:
            await RoverManager.initialize_obstacles(session_cls=session_cls, data=settings.INITIAL_OBSTACLES)
        # initialize rover
        try:
            if not await RoverManager.check_rover_already_landed(session_cls=session_cls):
                await RoverManager.initialize_rover(
                    session_cls=session_cls,
                    longitude=settings.START_POSTITION[0],
                    latitude=settings.START_POSTITION[1],
                    direction=settings.START_DIRECTION,
                )
                logger.info(
                    f"Rover successfully landed. "
                    f"Coord ({settings.START_POSTITION[0]}, {settings.START_POSTITION[1]})"
                )
        except custom_exc.RoverLandedInObstacleException:
            logger.critical("Rover landed on an obstacle. Startup aborted.")
            # sys.exit(1) — forceful shutdown, better to cancel lifespan
            raise RuntimeError("Rover landed in an obstacle. Server aborted.")
    yield
