import pytest

from managers.rover_manager import RoverPlanner
from schemas.enums import Direction

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.mark.parametrize(
    "start, cmd, expected",
    [
        ((0, 0, Direction.NORTH), "F", (0, 1, Direction.NORTH)),
        ((0, 0, Direction.NORTH), "B", (0, -1, Direction.NORTH)),
        ((1, 1, Direction.EAST),  "L", (1, 1, Direction.NORTH)),
        ((1, 1, Direction.SOUTH), "R", (1, 1, Direction.WEST)),
    ],
)
def test_get_new_state(start, cmd, expected):
    """
    Given an initial (x, y, direction) and a single command,
    get_new_state should return the correct updated coordinates
    and facing direction:

      - 'F' moves forward in the current direction.
      - 'B' moves backward.
      - 'L' and 'R' rotate the rover without changing position.
    """
    new = RoverPlanner.get_new_state(start, cmd)
    assert new == expected


def test_drive_sequence():
    """
    Verify that drive() yields the full sequence of states
    for a complex path string. Starting at (0,0) facing EAST
    and following "FFLFFR", the rover should visit:

      1. F -> (1,0,EAST)
      2. F -> (2,0,EAST)
      3. L -> (2,0,NORTH)
      4. F -> (2,1,NORTH)
      5. F -> (2,2,NORTH)
      6. R -> (2,2,EAST)
    """
    planner = RoverPlanner(0, 0, Direction.EAST)
    path = "FFLFFR"
    states = list(planner.drive(path))
    assert states == [
        (1, 0, Direction.EAST),
        (2, 0, Direction.EAST),
        (2, 0, Direction.NORTH),
        (2, 1, Direction.NORTH),
        (2, 2, Direction.NORTH),
        (2, 2, Direction.EAST),
    ]
