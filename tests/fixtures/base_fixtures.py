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


# class UserFixture(factory.alchemy.SQLAlchemyModelFactory):
#     class Meta:
#         model = models.User
#         sqlalchemy_session_factory = get_db_session
#         sqlalchemy_session = None
#         sqlalchemy_session_persistence = "commit"
#         sqlalchemy_get_or_create = ("id",)
#
#     id = constants.DEFAULT_USER_ID
#     date_of_birth = factory.LazyFunction(lambda: fake.date_of_birth(minimum_age=18))
#     first_name = factory.LazyFunction(lambda: fake.text(max_nb_chars=255))
#     last_name = factory.LazyFunction(lambda: fake.text(max_nb_chars=255))
#     email = factory.LazyFunction(lambda: fake.email())
#     password = factory.LazyFunction(lambda: fake.password())
#     sex = factory.LazyFunction(lambda: fake.enum(SexType))
