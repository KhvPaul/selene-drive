from sqlalchemy import orm as so
from sqlalchemy.ext import asyncio as sa_asyncio

from db import models
from managers.base_manager import BaseModelManager
from schemas import enums


class RoverManager(BaseModelManager):

    @classmethod
    async def initialize_rover(
        cls,
        session_cls: so.sessionmaker[sa_asyncio.AsyncSession],
        longitude: int,
        latitude: int,
        direction: enums.Direction,
    ) -> models.RoverState:
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
    async def execute_rover_commands(cls, session_cls: so.sessionmaker[sa_asyncio.AsyncSession], commands: str):
        ...
