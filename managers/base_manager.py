from db.db_api import base as base_db_api, models_db_api


class BaseModelManager:
    """
    Base class used to manage models
    """

    _db_api = base_db_api.DBApiBase()
    _rover_db_api = models_db_api.RoverStateDBAPI()
    _command_input_db_api = models_db_api.CommandInputDBAPI()
    _obstacle_db_api = models_db_api.ObstacleDBAPI()
