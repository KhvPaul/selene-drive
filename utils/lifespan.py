from contextlib import asynccontextmanager

from fastapi import FastAPI

from config import settings
from db.session import get_async_postgres_session
from logger import logger
from managers import RoverLandingHelper
from utils import exceptions as custom_exc


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with get_async_postgres_session() as session_cls:
        # initialize obstacles if exists predefined
        await RoverLandingHelper.prune_obstacles(session_cls=session_cls)
        if settings.INITIAL_OBSTACLES:
            await RoverLandingHelper.initialize_obstacles(session_cls=session_cls, data=settings.INITIAL_OBSTACLES)
        # initialize rover
        try:
            await RoverLandingHelper.initialize_rover(
                session_cls=session_cls,
                longitude=settings.START_POSITION[0],
                latitude=settings.START_POSITION[1],
                direction=settings.START_DIRECTION,
            )
            logger.info(
                f"Rover successfully landed. "
                f"Coord ({settings.START_POSITION[0]}, {settings.START_POSITION[1]})"
            )
        except custom_exc.RoverLandedInObstacleException as exc:
            logger.critical("Rover landed on an obstacle. Startup aborted.")
            # sys.exit(1) — forceful shutdown, better to cancel lifespan
            raise RuntimeError("Rover landed in an obstacle. Server aborted.")
    logger.info("Rover is ready to accept requests.")
    yield
