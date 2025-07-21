import pytest
from sqlalchemy import delete

from db.db_api.models_db_api import ObstacleDBAPI, RoverStateDBAPI
from db.models.models import Obstacle, RoverState
from managers.rover_manager import DBDataProvider, RoverManager, RoverPlanner
from schemas.enums import Direction

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_rover_manager_no_obstacle(session_cls):
    """
    Test that RoverManager.execute_rover_command completes the full path when there are no obstacles.

    Scenario:
      - Start with a clean database.
      - Seed an initial RoverState at (0,0) facing NORTH.
      - Issue the commands "FFRFF" (move forward twice, turn right, move forward twice).
      - Expect the final position to be (2, 2) facing EAST.
      - Expect no obstacle to be reported.
    """
    async with session_cls() as session:
        # Clean relevant tables
        for tbl in (RoverState, Obstacle):
            await session.execute(delete(tbl))
        await session.commit()

        # Seed landing position
        await RoverStateDBAPI.create_session(
            session, data={"longitude": 0, "latitude": 0, "direction": Direction.NORTH}, return_=True
        )
        await session.commit()

        provider = DBDataProvider(session)
        manager = RoverManager(provider, rover_planner=RoverPlanner, road="FFRFF")

        final_state, obstacle = await manager.execute_rover_command()
        # Path: F -> (0,1,N), F -> (0,2,N), R -> (0,2,E), F -> (1,2,E), F -> (2,2,E)
        assert final_state == (2, 2, Direction.EAST)
        assert obstacle is None


async def test_rover_manager_stops_on_obstacle(session_cls):
    """
    Test that RoverManager.execute_rover_command stops at the first obstacle encountered.

    Scenario:
      - Start with a clean database.
      - Seed an initial RoverState at (0,0) facing NORTH.
      - Insert a single obstacle at (0,2).
      - Issue the commands "FFF" (move forward three times).
      - Expect the rover to move to (0,1) then attempt (0,2) and stop.
      - Expect the reported obstacle coordinate to be (0,2).
    """
    async with session_cls() as session:
        # Clean relevant tables
        for tbl in (RoverState, Obstacle):
            await session.execute(delete(tbl))
        await session.commit()

        # Seed landing position
        await RoverStateDBAPI.create_session(
            session, data={"longitude": 0, "latitude": 0, "direction": Direction.NORTH}, return_=True
        )
        # Insert obstacle at (0,2)
        await ObstacleDBAPI.create_session(session, data={"longitude": 0, "latitude": 2})
        await session.commit()

        provider = DBDataProvider(session)
        manager = RoverManager(provider, rover_planner=RoverPlanner, road="FFF")

        final_state, obstacle = await manager.execute_rover_command()
        # Moves: (0,0)->(0,1), then (0,2) is blocked
        assert final_state == (0, 1, Direction.NORTH)
        assert obstacle == (0, 2)
