from db.db_api import base as base_db_api
from db.models import models


class RoverStateDBAPI(base_db_api.DBApiBase):
    model = models.RoverState


class CommandInputDBAPI(base_db_api.DBApiBase):
    model = models.CommandInput


class ObstacleDBAPI(base_db_api.DBApiBase):
    model = models.Obstacle
