from uvicorn import Config, Server
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn_worker import UvicornWorker

from config import settings
from routers import app_router, internal_router
from utils.lifespan import lifespan


app = FastAPI(
    debug=False,
    docs_url=f"/docs",
    openapi_url=f"/openapi.json",
    lifespan=lifespan,
)
app.openapi_version = "3.0.0"

app.include_router(app_router.router, prefix=f"{settings.API_V1_STR}")
app.include_router(internal_router.router, prefix=f"{settings.API_V1_STR}")


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ORIGINS,
    allow_origin_regex=r"^(http://|https://)?localhost:\d+$" if settings.DEBUG else None,
    allow_credentials=True,
    allow_methods=["POST", "GET", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)


class CustomUvicornWorker(UvicornWorker):
    CONFIG_KWARGS = dict(loop="uvloop", log_level=settings.LOG_LEVEL.lower(), access_log=settings.UVICORN_ACCESS_LOG)


if __name__ == "__main__":
    server = Server(
        Config(
            app,
            host=settings.SERVER_HOST,
            port=settings.SERVER_PORT,
            workers=settings.SERVER_WORKERS,
            loop="uvloop",
        ),
    )
    server.run()
