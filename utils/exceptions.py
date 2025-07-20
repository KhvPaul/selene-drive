import http

from fastapi.exceptions import HTTPException

from schemas import enums


class ObjectAlreadyExistsException(HTTPException):
    def __init__(self):
        super(HTTPException, self).__init__(
            status_code=http.HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="Object Already Exists",
        )


class ObjectWasNotCreatedException(HTTPException):
    def __init__(self):
        super(HTTPException, self).__init__(
            status_code=http.HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="Object was not created",
        )


class SomethingWentWrongException(HTTPException):
    def __init__(self):
        super(HTTPException, self).__init__(
            status_code=http.HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="Something went wrong",
        )


class NotFoundException(HTTPException):
    def __init__(self):
        super(HTTPException, self).__init__(
            status_code=http.HTTPStatus.NOT_FOUND,
            detail="Not found",
        )


class RoverLandedInObstacleException(Exception):
    ...


class RoverBlockedByObstacleException(Exception):
    def __init__(self, longitude: int, latitude: int, direction: enums.Direction):
        super().__init__(f"Rover blocked by obstacle at ({longitude}, {latitude}, {direction})")
