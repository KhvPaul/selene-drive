import uuid

from pydantic import BaseModel, ConfigDict


class ResponseBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ResponseOk(ResponseBaseModel):
    message: str = "OK"


class IdMixin:
    id: uuid.UUID
