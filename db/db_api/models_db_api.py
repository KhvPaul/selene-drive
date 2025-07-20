from db.db_api import base as base_db_api
from db.models import models


class RobotStateDBAPI(base_db_api.DBApiBase):
    model = models.RobotState


class CommandLogDBAPI(base_db_api.DBApiBase):
    model = models.CommandLog


class ObstaclesDBAPI(base_db_api.DBApiBase):
    model = models.Obstacles
