from sqlalchemy import orm as so

from .mixins import PkModelMixin, CreateTimeModelMixin, TimestampModelMixin


class Base(so.DeclarativeBase):
    ...
