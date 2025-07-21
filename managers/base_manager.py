from db.db_api import base as base_db_api
from db.db_api import models_db_api


class BaseModelManager:
    """
    Base class used to manage models
    """

    _db_api = base_db_api.DBApiBase()
    _rover_db_api = models_db_api.RoverStateDBAPI()
    _rover_state_to_command_input_db_api = models_db_api.RoverStateToCommandInputDBAPI()
    _command_input_db_api = models_db_api.CommandInputDBAPI()
    _obstacle_db_api = models_db_api.ObstacleDBAPI()
