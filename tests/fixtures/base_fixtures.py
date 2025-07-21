import random

import factory  # noqa: F401
import faker

from db import models  # noqa: F401
from schemas import enums  # noqa: F401


def _get_db_session():
    # Mock me!
    pass


def get_db_session():
    # The function is necessary due to the specific operation of mock
    return _get_db_session()


fake = faker.Faker()


class RoverStateFixture(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.RoverState
        sqlalchemy_session_factory = get_db_session
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "commit"

    longitude = factory.LazyFunction(fake.pyint)
    latitude = factory.LazyFunction(fake.pyint)
    direction = factory.LazyFunction(lambda: fake.enum(enums.Direction))


class CommandInputFixture(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.CommandInput
        sqlalchemy_session_factory = get_db_session
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "commit"
        sqlalchemy_get_or_create = ("id",)

    command = factory.LazyFunction(
        lambda: ''.join(random.choice('FBLR') for _ in range(random.randint(500, 100_000)))
    )


class ObstacleFixture(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.Obstacle
        sqlalchemy_session_factory = get_db_session
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "commit"

    longitude = factory.LazyFunction(fake.pyint)
    latitude = factory.LazyFunction(fake.pyint)
