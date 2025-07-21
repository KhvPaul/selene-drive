import enum
import typing as t


class Direction(str, enum.Enum):
    NORTH = "NORTH"
    SOUTH = "SOUTH"
    EAST = "EAST"
    WEST = "WEST"

    def move_delta(self, command: str) -> tuple[int, int]:
        if command not in ("F", "B"):
            raise ValueError("Invalid movement command")
        forward = command == "F"
        match self:
            case Direction.NORTH:
                return (0, 1) if forward else (0, -1)
            case Direction.SOUTH:
                return (0, -1) if forward else (0, 1)
            case Direction.EAST:
                return (1, 0) if forward else (-1, 0)
            case Direction.WEST:
                return (-1, 0) if forward else (1, 0)
        return 0, 0

    def rotate(self, rotate_cmd: str) -> t.Self:
        directions = [Direction.EAST, Direction.NORTH, Direction.WEST, Direction.SOUTH]
        idx = directions.index(self)
        if rotate_cmd == "L":
            return directions[(idx + 1) % 4]
        if rotate_cmd == "R":
            return directions[(idx - 1) % 4]
        raise ValueError("Invalid rotate command")
