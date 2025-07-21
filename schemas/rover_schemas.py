from pydantic import field_validator

from . import common, enums


class RoverStateBase(common.BaseModel):
    longitude: int
    latitude: int
    direction: enums.Direction


class RoverStateResponse(common.ResponseBaseModel, RoverStateBase):
    ...


class RoverCommandsRequest(common.BaseModel):
    command: str

    @field_validator("command")
    def validate_command(cls, v):
        allowed = {"F", "B", "R", "L"}
        if not set(v).issubset(allowed):
            raise ValueError("Command may only contain characters: F, B, R, L")
        return v


class ObstacleResponseModel(common.ResponseBaseModel):
    longitude: int
    latitude: int


class RoverStateAfterCommandResponse(common.ResponseBaseModel):
    rover_state: RoverStateResponse
    obstacle: ObstacleResponseModel | None
