import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.ext import asyncio as sa_asyncio

from db.db_api import base as base_db_api
from db.models import models


class RoverStateDBAPI(base_db_api.DBApiBase):
    model = models.RoverState


class RoverStateToCommandInputDBAPI(base_db_api.DBApiBase):
    model = models.RoverStateToCommandInput


class CommandInputDBAPI(base_db_api.DBApiBase):
    model = models.CommandInput


class ObstacleDBAPI(base_db_api.DBApiBase):
    model = models.Obstacle

    @classmethod
    async def check_intersection_session(
        cls, session: sa_asyncio.AsyncSession, coords: set[tuple[int, int]]
    ) -> bool:
        longitudes, latitudes = zip(*coords, strict=True) if coords else ([], [])

        unnested = sa.func.unnest(
            pg.array(longitudes, type_=pg.ARRAY(pg.INTEGER)),
            pg.array(latitudes, type_=pg.ARRAY(pg.INTEGER))
        ).table_valued("longitude", "latitude").alias("t")

        stmt = sa.select(sa.literal(True)).where(
            sa.exists(
                sa.select(sa.literal(1))
                .select_from(
                    unnested.join(
                        models.Obstacle,
                        sa.and_(
                            models.Obstacle.longitude == sa.column("longitude"),
                            models.Obstacle.latitude == sa.column("latitude")
                        )
                    )
                )
            )
        )
        return await cls.execute_session(session=session, stmt=stmt, all_=False)

    @classmethod
    async def retrieve_intersection_session(
        cls, session: sa_asyncio.AsyncSession, coords: set[tuple[int, int]]
    ) -> list[model]:
        longitudes, latitudes = zip(*coords, strict=True) if coords else ([], [])

        unnested = sa.func.unnest(
            pg.array(longitudes, type_=pg.ARRAY(pg.INTEGER)),
            pg.array(latitudes, type_=pg.ARRAY(pg.INTEGER))
        ).table_valued("longitude", "latitude").alias("t")

        stmt = (
            sa.select(models.Obstacle.longitude, models.Obstacle.latitude)
            .select_from(
                unnested.join(
                    models.Obstacle,
                    sa.and_(
                        models.Obstacle.longitude == sa.column("longitude"),
                        models.Obstacle.latitude == sa.column("latitude")
                    )
                )
            )
        )
        return await cls.execute_session(session=session, stmt=stmt, all_=True, mapping=True)
