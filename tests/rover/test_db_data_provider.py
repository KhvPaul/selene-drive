import pytest
import sqlalchemy as sa

from db.db_api.models_db_api import ObstacleDBAPI, RoverStateDBAPI
from db.models.models import CommandInput, Obstacle, RoverState, RoverStateToCommandInput
from managers.rover_manager import DBDataProvider, RoverPlanner
from schemas.enums import Direction

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_save_and_retrieve_and_process(session_cls):
    """
    Verify that DBDataProvider can:
      1. Save a new command to command_inputs.
      2. Retrieve the current rover state.
      3. Process a small sequence of moves:
         - Insert the resulting RoverState rows.
         - Insert the corresponding RoverStateToCommandInput mappings.
    Steps:
    - Clean the RoverState, CommandInput, and mapping tables.
    - Seed an initial RoverState at (0,0,NORTH).
    - Call save_command("LRF") and assert command_obj is set.
    - Call retrieve_current_state() and verify it returns (0,0,NORTH).
    - Generate the three-step path for "LRF" via RoverPlanner.
    - Call process_pass() with those coordinates.
    - Assert that the DB contains one initial row plus exactly those three new rows.
    - Assert that each new row has a corresponding entry in rover_states_to_command_inputs.
    """
    async with session_cls() as session:
        # Clean out relevant tables
        for tbl in (RoverState, CommandInput, RoverStateToCommandInput):
            await session.execute(sa.delete(tbl))
        await session.commit()

        provider = DBDataProvider(session)

        # Seed the initial rover landing at origin facing NORTH
        await RoverStateDBAPI.create_session(
            session, data={"longitude": 0, "latitude": 0, "direction": Direction.NORTH}, return_=True
        )
        await session.commit()

        # Save a new command
        await provider.save_command("LRF")
        assert provider.command_obj.command == "LRF"

        # Retrieve the current state from DB
        cur = await provider.retrieve_current_state()
        assert cur == (0, 0, Direction.NORTH)

        # Simulate a small path of three moves
        coords = list(RoverPlanner(0, 0, Direction.NORTH).drive("LRF"))
        await provider.process_pass(coords)
        await session.commit()

        # Verify that rover_states contains the initial landing plus the three new states
        result = await session.execute(sa.select(RoverState).order_by(RoverState.id))
        all_states = result.scalars().all()
        # Skip the first row (initial state), compare the rest
        inserted = [(r.longitude, r.latitude, r.direction) for r in all_states][1:]
        assert inserted == coords

        # Verify that each inserted state has a mapping to the saved command
        result = await session.execute(sa.select(RoverStateToCommandInput))
        mappings = result.scalars().all()
        assert len(mappings) == len(coords)
        for m in mappings:
            assert m.command_input_id == provider.command_obj.id


async def test_check_for_obstacle(session_cls):
    """
    Ensure that DBDataProvider.check_for_obstacle correctly:
      - Detects the first collision index in a list of coordinates.
      - Returns None when no obstacle is present.
    Steps:
    - Clean the obstacles table.
    - Insert two obstacles at (1,1) and (3,3).
    - Build a list of coords that includes both obstacle points.
    - Assert that check_for_obstacle returns the tuple (index, (x,y)) for the first obstacle.
    - Assert that a fully safe coords list returns None.
    """
    async with session_cls() as session:
        # Remove any existing obstacles
        await session.execute(sa.delete(Obstacle))
        # Insert obstacles at (1,1) and (3,3)
        await ObstacleDBAPI.create_session(session, data={"longitude": 1, "latitude": 1})
        await ObstacleDBAPI.create_session(session, data={"longitude": 3, "latitude": 3})
        await session.commit()

        provider = DBDataProvider(session)

        # Construct a path that collides at index 1
        coords = [(0, 0), (1, 1), (2, 2), (3, 3)]
        result = await provider.check_for_obstacle(coords)
        # Should detect obstacle at (1,1) with index 1
        assert result == (1, (1, 1))

        # Now test a path with no intersections
        coords2 = [(5, 5), (6, 6)]
        assert await provider.check_for_obstacle(coords2) is None
