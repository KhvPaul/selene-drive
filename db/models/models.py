import uuid

import sqlalchemy as sa
from sqlalchemy import orm as so
from sqlalchemy.dialects import postgresql as pg

from .mixins import CreateTimeModelMixin, PkModelMixin, TimestampModelMixin  # noqa: F401
from schemas import enums


class Base(so.DeclarativeBase):  # noqa: F841
    ...


class RoverState(Base, PkModelMixin, CreateTimeModelMixin):
    """

    """
    __tablename__ = "rover_states"

    longitude: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, comment="Rover current longitude")
    latitude: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, comment="Rover current latitude")
    direction: so.Mapped[enums.Direction] = so.mapped_column(
        pg.ENUM(enums.Direction, name="direction_type"), nullable=False, comment="Rover direction"
    )


class CommandInput(Base, PkModelMixin, CreateTimeModelMixin):
    __tablename__ = "command_inputs"

    command: so.Mapped[str] = so.mapped_column(sa.String, nullable=False, comment="Inputted command")


class RoverStateToCommandInput(Base):
    """"""
    __tablename__ = "rover_states_to_command_inputs"
    __table_args__ = (
        sa.PrimaryKeyConstraint("rover_state_id", "command_input_id", name="rover_state_id_command_input_id_pkey"),
    )

    rover_state_id: so.Mapped[uuid.UUID] = so.mapped_column(pg.UUID, nullable=False, comment="Rover state ID")
    command_input_id: so.Mapped[uuid.UUID] = so.mapped_column(pg.UUID, nullable=False, comment="Command input ID")


class Obstacle(Base, PkModelMixin, CreateTimeModelMixin):
    __tablename__ = "obstacles"

    longitude: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, comment="Rover current longitude")
    latitude: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, comment="Rover current latitude")
