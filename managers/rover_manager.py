from sqlalchemy import orm as so, exc as sa_exc
from sqlalchemy.ext import asyncio as sa_asyncio

from db import models
from managers.base_manager import BaseModelManager
from schemas import enums
from utils import exceptions as custom_exc


class RoverManager(BaseModelManager):

    @classmethod
    async def initialize_obstacles(
        cls, session_cls: so.sessionmaker[sa_asyncio.AsyncSession], data: tuple[int, int]
    ) -> None:
        """
        Initialize obstacles by bulk-inserting predefined (longitude, latitude) coordinates.
        """
        return await RoverManager._obstacle_db_api.bulk_create(
            session_cls=session_cls,
            data=[{"longitude": longitude, "latitude": latitude} for longitude, latitude in data],
        )

    @classmethod
    async def initialize_rover(
        cls,
        session_cls: so.sessionmaker[sa_asyncio.AsyncSession],
        longitude: int,
        latitude: int,
        direction: enums.Direction,
    ) -> models.RoverState:
        """
        Initialize the rover's first position and direction.
        Raise an exception if the rover would land on an obstacle.
        """
        if cls._obstacle_db_api.retrieve(
            session_cls=session_cls,
            condition=(
                cls._obstacle_db_api.model.longitude == longitude, cls._obstacle_db_api.model.latitude == latitude
            )
        ):
            raise custom_exc.RoverLandedInObstacleException()
        return await cls._rover_db_api.create(
            session_cls=session_cls,
            data={"longitude": longitude, "latitude": latitude, "direction": direction},
            return_=True,
        )

    @classmethod
    async def check_rover_already_landed(cls, session_cls: so.sessionmaker[sa_asyncio.AsyncSession]) -> bool:
        return await cls._rover_db_api.exists(session_cls=session_cls)


    @classmethod
    async def retrieve_rover_state(cls, session_cls: so.sessionmaker[sa_asyncio.AsyncSession]) -> models.RoverState:
        return await cls._rover_db_api.retrieve(session_cls=session_cls)

    @classmethod
    async def execute_rover_commands(
        cls, session_cls: so.sessionmaker[sa_asyncio.AsyncSession], commands: str
    ) -> models.RoverState:
        """
        Execute a sequence of rover commands (F, B, L, R) step by step.
        The rover state is stored in the database in batches of 1000.
        If the rover encounters an obstacle (detected by trigger), it stops and raises an exception.
        Returns the last successful rover state.
        """
        async with session_cls() as session:
            rover_state = await cls._rover_db_api.retrieve_session(session=session)
            x, y, direction = rover_state.longitude, rover_state.latitude, rover_state.direction

            batch: list[dict] = []

            def rotate(dir_: enums.Direction, rotate_direction: str) -> enums.Direction:
                """"Returns new direction after rotating 90 degrees left or right."""
                directions = [enums.Direction.EAST, enums.Direction.NORTH, enums.Direction.WEST, enums.Direction.SOUTH]
                idx = directions.index(dir_)
                return directions[(idx + 1) % 4] if rotate_direction == "L" else directions[(idx - 1) % 4]

            for command in commands:
                if command in ("L", "R"):
                    direction = direction.rotate(command)
                else:
                    dx, dy = direction.move_delta(command)
                    x += dx
                    y += dy
                batch.append({"longitude": x, "latitude": y, "direction": direction})

                # Insert in batches
                if len(batch) == 1000:
                    try:
                        await cls._rover_db_api.bulk_create(session_cls=session_cls, data=batch)
                        batch.clear()
                    except sa_exc.IntegrityError:
                        # Find the exact failing command in batch
                        x, y, direction = await cls._binary_insert_with_fail_safe(session_cls=session_cls, batch=batch)
                        raise custom_exc.RoverBlockedByObstacleException(longitude=x, latitude=y, direction=direction)
            # Flush remaining steps
            if batch:
                try:
                    await cls._rover_db_api.bulk_create(session_cls=session_cls, data=batch)
                except sa_exc.IntegrityError:
                    x, y, direction = await cls._binary_insert_with_fail_safe(session_cls=session_cls, batch=batch)
                    raise custom_exc.RoverBlockedByObstacleException(longitude=x, latitude=y, direction=direction)

            return models.RoverState(longitude=x, latitude=y, direction=direction)

    @classmethod
    async def _binary_insert_with_fail_safe(cls, session_cls, batch: list[dict]) -> tuple[int, int, enums.Direction]:
        """
        Performs a binary search over a batch to find the first entry that violates
        the trigger constraint (i.e., hits an obstacle).
        Returns the blocked (x, y, direction) that failed the insert.
        """
        lower, upper = 0, len(batch)
        while lower < upper:
            mid = (lower + upper) // 2
            try:
                await cls._rover_db_api.bulk_create(session_cls=session_cls, data=batch[:mid + 1])
                lower = mid + 1
            except sa_exc.IntegrityError:
                upper = mid
        if lower > 0:
            await cls._rover_db_api.bulk_create(session_cls=session_cls, data=batch[:lower])
        bad = batch[lower]
        return bad["longitude"], bad["latitude"], bad["direction"]
