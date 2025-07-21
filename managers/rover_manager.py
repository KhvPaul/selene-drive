from abc import ABC, abstractmethod
from collections.abc import Generator
from itertools import batched

from sqlalchemy import orm as so
from sqlalchemy.ext import asyncio as sa_asyncio

from db import models
from db.db_api import models_db_api
from managers.base_manager import BaseModelManager
from schemas import enums
from utils import exceptions as custom_exc


class RoverLandingHelper(BaseModelManager):

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
        if await cls._obstacle_db_api.retrieve(
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
    async def prune_obstacles(cls, session_cls: so.sessionmaker[sa_asyncio.AsyncSession]) -> None:
        return await cls._obstacle_db_api.delete(session_cls=session_cls, condition=())

    @classmethod
    async def initialize_obstacles(
        cls, session_cls: so.sessionmaker[sa_asyncio.AsyncSession], data: tuple[int, int]
    ) -> None:
        """
        Initialize obstacles by bulk-inserting predefined (longitude, latitude) coordinates.
        """
        return await cls._obstacle_db_api.bulk_create(
            session_cls=session_cls,
            data=[{"longitude": longitude, "latitude": latitude} for longitude, latitude in data],
        )

    @classmethod
    async def check_rover_already_landed(cls, session_cls: so.sessionmaker[sa_asyncio.AsyncSession]) -> bool:
        return await cls._rover_db_api.exists(session_cls=session_cls)


directions = [direction.value for direction in enums.Direction]


class ABCRoverPlanner(ABC):
    @abstractmethod
    def __init__(self, lat: int, lng: int, direction: str) -> None:
        pass

    @abstractmethod
    def drive(self, coords: (int, int, enums.Direction)) -> Generator[tuple[int, int, enums.Direction]]:
        pass


class RoverPlanner(ABCRoverPlanner):
    def __init__(self, lat: int, lng: int, direction: enums.Direction) -> None:
        self.lat = lat
        self.lng = lng
        self.direction = direction

    @staticmethod
    def get_new_state(old_state: (int, int, enums.Direction), i: str) -> (int, int, enums.Direction):
        x = old_state[0]
        y = old_state[1]
        direction = old_state[2]

        if i in ("L", "R"):
            direction = direction.rotate(i)
        else:
            delta_x, delta_y = direction.move_delta(i)
            x += delta_x
            y += delta_y

        return x, y, direction

    def drive(self, road: str) -> Generator[tuple[int, int, enums.Direction]]:
        state = (self.lat, self.lng, self.direction)
        for i in road:
            state = self.get_new_state(state, i)
            yield state


class ABCDataProvider(ABC):  # DataProvider
    @abstractmethod
    async def retrieve_current_state(self) -> (int, int, enums.Direction):
        pass

    @abstractmethod
    async def check_for_obstacle(self, coords: (int, int)) -> tuple[int, (int, int)] | None:
        pass

    @abstractmethod
    async def process_pass(self, coords: (int, int, enums.Direction)):
        pass

    @abstractmethod
    async def save_command(self, command: str):
        pass


class DBDataProvider(ABCDataProvider):  # DBDataProvider
    command_obj = None
    _rover_state_db_api = models_db_api.RoverStateDBAPI()
    _rover_state_to_command_input_db_api = models_db_api.RoverStateToCommandInputDBAPI()
    _command_input_db_api = models_db_api.CommandInputDBAPI()
    _obstacle_db_api = models_db_api.ObstacleDBAPI()

    def __init__(self, session: sa_asyncio.AsyncSession):
        self.session = session

    async def retrieve_current_state(self) -> (int, int, enums.Direction):
        rover_state: models.RoverState = await self._rover_state_db_api.retrieve_session(
            session=self.session, order_fields=(self._rover_state_db_api.model.id.desc(),)
        )
        return rover_state.longitude, rover_state.latitude, rover_state.direction

    async def check_for_obstacle(self, coords: (int, int)) -> tuple[int, (int, int)] | None:
        has_obst = await self._obstacle_db_api.check_intersection_session(session=self.session, coords=coords)

        if has_obst:
            obs_coord_result = await self._obstacle_db_api.retrieve_intersection_session(
                session=self.session, coords=coords
            )
            obs_coords = {(o.longitude, o.latitude) for o in obs_coord_result}
            for idx, (x, y) in enumerate(coords):
                if (x, y) in obs_coords:
                    return coords.index((x, y)), (x, y)
        return None

    async def process_pass(self, coords: (int, int, enums.Direction)):
        coords_objs = await self._rover_state_db_api.bulk_create_session(
            session=self.session,
            data=[{"longitude": longitude, "latitude": latitude, "direction": direction} for longitude, latitude, direction in coords],
            return_=True
        )
        await self._rover_state_to_command_input_db_api.bulk_create_session(
            session=self.session,
            data=[
                {
                    "rover_state_id": state.id,
                    "command_input_id": self.command_obj.id
                } for state in coords_objs
            ],
        )

    async def save_command(self, command: str):
        self.command_obj = await self._command_input_db_api.create_session(
            session=self.session, data={"command": command}, return_=True
        )


class RoverManager:
    chunk_size = 1000

    def __init__(self, data_provider: ABCDataProvider, rover_planner: type[ABCRoverPlanner], road: str):
        self.data_provider = data_provider
        self.rover_planner = rover_planner
        self.road = road

    async def execute_rover_command(self) -> ((int, int, enums.Direction), tuple[int, int] | None):
        await self.data_provider.save_command(self.road)

        current_state = await self.data_provider.retrieve_current_state()
        rover = self.rover_planner(*current_state).drive(self.road)

        result = (current_state, None)
        for road_chunk in batched(rover, self.chunk_size):
            coordinates = [(i[0], i[1]) for i in road_chunk]
            has_obst = await self.data_provider.check_for_obstacle(coordinates)
            if has_obst:
                index = has_obst[0]
                success_chunk = road_chunk[:index]
            else:
                success_chunk = road_chunk
            await self.data_provider.process_pass(success_chunk)

            if has_obst:
                result = (success_chunk[-1], has_obst[1])
                break
            result = (success_chunk[-1], None)

        return result
