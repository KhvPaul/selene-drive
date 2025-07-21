from unittest import mock

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import scoped_session, sessionmaker

from schemas import enums
from tests.fixtures import base_fixtures

pytestmark = pytest.mark.asyncio(loop_scope="session")

async def test_rover_state(session_cls, client: AsyncClient):
    """
    Test that GET /api/v1/rover returns the current rover state from the database.

    This test:
    - Mocks out the SQLAlchemy session factory so that the fixture
      uses our in-memory or test DB.
    - Uses Factory Boy to insert one RoverState.
    - Calls the endpoint and verifies status code and JSON payload.
    """
    # Prepare a synchronous session for the fixture
    sync_session_cls = scoped_session(sessionmaker(bind=session_cls.sync_engine))
    with (
        sync_session_cls() as sync_session,
        # Patch the factory to return our sync_session
        mock.patch("tests.fixtures.base_fixtures._get_db_session", lambda: sync_session),
    ):
        # Create exactly one rover state in DB
        rover_state = base_fixtures.RoverStateFixture()

        # Call the API
        resp = await client.get("/api/v1/rover")
        assert resp.status_code == 200
        # Verify JSON matches the record we inserted
        assert resp.json() == {
            "direction": rover_state.direction,
            "longitude": rover_state.longitude,
            "latitude": rover_state.latitude,
        }


@pytest.mark.parametrize(
    "command, obstacles_data, expected_result",
    [
        # Case 1: drive freely, no obstacle in path
        (
            "BBBBBLFFFFF",
            ((1, 1), (2, 2)),  # obstacles at (1,1) and (2,2) but our route avoids them
            {
                "rover_state": {
                    "longitude": -5,
                    "latitude": -5,
                    "direction": enums.Direction.WEST.value,
                },
                "obstacle": None,
            },
        ),
        # Case 2: hit an obstacle at (5,5)
        (
            "FRFLFRFLFRFLFRFLFRFLFRFLFRFLFRFLFRFLFR",
            ((5, 5),),  # only obstacle at (5,5)
            {
                "rover_state": {
                    "longitude": 4,
                    "latitude": 5,
                    "direction": enums.Direction.EAST.value,
                },
                "obstacle": {"longitude": 5, "latitude": 5},
            },
        ),
    ],
)
async def test_execute_command(session_cls, client: AsyncClient, command, obstacles_data, expected_result):
    """
    Test POST /api/v1/rover/execute_command for both obstacle-free and obstacle-hit scenarios.

    For each scenario:
    - Inserts one initial RoverState at (0,0,NORTH).
    - Inserts obstacles at the given coordinates.
    - Calls GET /rover to confirm initial state.
    - Calls POST /rover/execute_command with `command`.
    - Verifies:
      * HTTP 200
      * JSON payload contains `rover_state` matching the last safe position & direction.
      * If an obstacle was in the path, `obstacle` matches its coordinates.
    - Finally calls GET /rover again to confirm state persisted.
    """
    # Prepare a synchronous session for the fixture
    sync_session_cls = scoped_session(sessionmaker(bind=session_cls.sync_engine))
    with (
        sync_session_cls() as sync_session,
        mock.patch("tests.fixtures.base_fixtures._get_db_session", lambda: sync_session),
    ):
        # Insert initial rover state at origin facing NORTH
        rover_state = base_fixtures.RoverStateFixture(longitude=0, latitude=0, direction=enums.Direction.NORTH)
        # Insert each obstacle
        obstacles = [base_fixtures.ObstacleFixture(longitude=lon, latitude=lat) for lon, lat in obstacles_data]

        # Confirm initial GET
        resp = await client.get("/api/v1/rover")
        assert resp.status_code == 200
        assert resp.json() == {
            "direction": rover_state.direction,
            "longitude": rover_state.longitude,
            "latitude": rover_state.latitude,
        }

        # Execute the command string
        resp = await client.post("/api/v1/rover/execute_command", json={"command": command})
        assert resp.status_code == 200
        # Check endpoint response matches expectation
        assert resp.json() == expected_result

        # Verify that the final state was persisted
        resp2 = await client.get("/api/v1/rover")
        assert resp2.status_code == 200
        assert resp2.json() == expected_result["rover_state"]
