from sqlalchemy import orm as so

from .mixins import CreateTimeModelMixin, PkModelMixin, TimestampModelMixin  # noqa: F401


class Base(so.DeclarativeBase):  # noqa: F841
    ...
