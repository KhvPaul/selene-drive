import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy import orm as so
from sqlalchemy.dialects import postgresql as pg


class PkModelMixin:
    @so.declared_attr
    def id(cls) -> so.Mapped[uuid.UUID]:
        return so.mapped_column(
            pg.UUID,
            default=uuid.uuid4,
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
            index=True,
            comment="Unique identifier for each record",
        )


class CreateTimeModelMixin:
    @so.declared_attr
    def create_time(cls) -> so.Mapped[datetime.datetime]:
        return so.mapped_column(
            pg.TIMESTAMP(timezone=False),
            default=sa.func.now(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        )


class UpdateTimeModelMixin:
    @so.declared_attr
    def update_time(cls) -> so.Mapped[datetime.datetime]:
        return so.mapped_column(
            pg.TIMESTAMP(timezone=False),
            default=sa.func.now(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            onupdate=sa.func.now(),
            nullable=False,
        )


class TimestampModelMixin(CreateTimeModelMixin, UpdateTimeModelMixin):
    pass
