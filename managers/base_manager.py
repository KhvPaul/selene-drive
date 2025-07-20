from db.db_api import base as base_db_api


class BaseModelManager:
    """
    Base class used to manage models
    """

    _db_api = base_db_api.DBApiBase()
