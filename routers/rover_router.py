from fastapi import APIRouter

from managers import DBDataProvider, RoverManager, RoverPlanner
from schemas import rover_schemas as pyd_mod_rover
from schemas.rover_schemas import RoverStateResponse
from utils.annotations import AsyncSession, AsyncSessionCls

router = APIRouter(prefix="/rover", tags=["Rover"])


@router.get("", response_model=pyd_mod_rover.RoverStateResponse)
async def retrieve_current_state(session: AsyncSession):
    longitude, latitude, direction = await DBDataProvider(session=session).retrieve_current_state()
    return RoverStateResponse(longitude=longitude, latitude=latitude, direction=direction)



@router.post("/execute_command", response_model=pyd_mod_rover.RoverStateAfterCommandResponse)
async def execute_rover_command(session_cls: AsyncSessionCls, command: pyd_mod_rover.RoverCommandsRequest):
    async  with session_cls() as session:
        res = await RoverManager(
            data_provider=DBDataProvider(session=session),
            rover_planner=RoverPlanner,
            road=command.command,
        ).execute_rover_command()
        await session.commit()
    return pyd_mod_rover.RoverStateAfterCommandResponse(
        rover_state=pyd_mod_rover.RoverStateResponse(longitude=res[0][0], latitude=res[0][1], direction=res[0][2]),
        obstacle=pyd_mod_rover.ObstacleResponseModel(longitude=res[1][0], latitude=res[1][1]) if res[1] else None,
    )
