import http

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from managers.base_manager import BaseModelManager
from schemas import common as pyd_mod_common
from utils.annotations import AsyncSession


manager = BaseModelManager()

OK = {"message": "OK"}
OK_RESPONSE = JSONResponse(content=OK, status_code=http.HTTPStatus.CREATED)
router = APIRouter(prefix="/internal", tags=["Internal"])


@router.get("/health_check")
def hello_world():
    return {"message": "Hello, World!"}


@router.get("/ping_db", response_model=pyd_mod_common.ResponseOk)
async def ping_db(session_cls: AsyncSession):
    await manager._db_api.ping(session_cls=session_cls)
    return OK_RESPONSE
