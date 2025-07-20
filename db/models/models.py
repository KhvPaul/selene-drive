from sqlalchemy import orm as so

from .mixins import PkModelMixin, CreateTimeModelMixin, TimestampModelMixin  # noqa: F401


class Base(so.DeclarativeBase):  # noqa: F841
    ...
