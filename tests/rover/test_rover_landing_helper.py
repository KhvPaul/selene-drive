import pytest

from db.db_api.models_db_api import ObstacleDBAPI
from managers.rover_manager import RoverLandingHelper
from schemas.enums import Direction
from utils.exceptions import RoverLandedInObstacleException

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_prune_and_initialize_obstacles_and_rover(session_cls):
    """
    Test that RoverLandingHelper correctly prunes, initializes obstacles, and lands the rover.

    This covers three scenarios:
      1. prune_obstacles + initialize_obstacles:
         - Clears the obstacles table.
         - Bulk-inserts a given list of obstacle coordinates.
         - Verifies that check_intersection_session detects those obstacles.
      2. initialize_rover on an empty field:
         - After pruning obstacles again, lands the rover at (0,0) facing EAST.
         - Asserts the returned RoverState has the correct coords and direction.
      3. initialize_rover on an occupied field:
         - Prunes then inserts a single obstacle at (5,5).
         - Attempts to land the rover on (5,5) and expects a RoverLandedInObstacleException.
    """
    # start with a clean obstacles table
    async with session_cls() as session:
        # prune any existing
        await RoverLandingHelper.prune_obstacles(session_cls=session_cls)
        # then initialize two obstacles
        obs = [(10, 20), (30, 40)]
        await RoverLandingHelper.initialize_obstacles(session_cls=session_cls, data=tuple(obs))

        # verify obstacles were inserted
        found = await ObstacleDBAPI.check_intersection_session(session=session, coords=set(obs))
        assert found is True

        # clean up for landing tests
        await RoverLandingHelper.prune_obstacles(session_cls=session_cls)

    # landing on a free spot should succeed
    state = await RoverLandingHelper.initialize_rover(
        session_cls=session_cls, longitude=0, latitude=0, direction=Direction.EAST
    )
    assert state.longitude == 0 and state.latitude == 0
    assert state.direction == Direction.EAST

    # landing on an obstacle should raise
    await RoverLandingHelper.prune_obstacles(session_cls=session_cls)
    await RoverLandingHelper.initialize_obstacles(session_cls=session_cls, data=((5, 5),))
    with pytest.raises(RoverLandedInObstacleException):
        await RoverLandingHelper.initialize_rover(
            session_cls=session_cls,
            longitude=5,
            latitude=5,
            direction=Direction.SOUTH,
        )


async def test_check_rover_already_landed(session_cls):
    """
    Test that check_rover_already_landed correctly reports whether the rover has been initialized.

    Steps:
      - Initially, no rover_states exist, so it should return False.
      - After initialize_rover, it should return True.
    """
    # no rover yet => False
    exists = await RoverLandingHelper.check_rover_already_landed(session_cls=session_cls)
    assert exists is False

    # land the rover
    _ = await RoverLandingHelper.initialize_rover(
        session_cls=session_cls, longitude=1, latitude=1, direction=Direction.NORTH
    )
    # now it should report True
    exists = await RoverLandingHelper.check_rover_already_landed(session_cls=session_cls)
    assert exists is True
