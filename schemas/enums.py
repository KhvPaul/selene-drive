import enum


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

    def rotate(self, rotate_cmd: str) -> "Direction":
        directions = [Direction.EAST, Direction.NORTH, Direction.WEST, Direction.SOUTH]
        idx = directions.index(self)
        if rotate_cmd == "L":
            return directions[(idx + 1) % 4]
        elif rotate_cmd == "R":
            return directions[(idx - 1) % 4]
        raise ValueError("Invalid rotate command")