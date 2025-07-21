import os
import typing as t

from dotenv import load_dotenv
from pydantic import Field, PostgresDsn, model_validator
from pydantic_settings import BaseSettings

from schemas import enums

load_dotenv()


class Settings(BaseSettings):
    BASE_DIR: str = os.path.dirname(os.path.realpath(__file__))

    API_V1_STR: str | None = "/api/v1"

    OAUTH2_TOKEN_URL: str | None = None

    SERVER_PORT: int = 8000
    SERVER_HOST: str = "0.0.0.0"
    SERVER_WORKERS: int = 2
    LANGUAGE: str = "en_US"
    ORIGINS: list | str = Field(default_factory=lambda *x: x.split(",") if x else ["*"])

    DEBUG: bool | None = Field(default_factory=lambda *x: x in ("1", "true", "True", "y"))
    ECHO_QUERY: bool | None = Field(default_factory=lambda *x: x in ("1", "true", "True", "y"))
    LOG_LEVEL: str = "DEBUG"
    UVICORN_ACCESS_LOG: bool = True

    # database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "postgres"
    DATABASE_ENDPOINT: PostgresDsn | None = None
    ASYNC_DATABASE_ENDPOINT: PostgresDsn | None = None

    DATABASE_MAX_CONNECTIONS: int = 100
    DATABASE_CONNECTION_RECYCLE: int = 3600

    @model_validator(mode="after")
    def assemble_db_connection(self) -> t.Self:
        if isinstance(self.DATABASE_ENDPOINT, str):
            return self
        self.DATABASE_ENDPOINT = PostgresDsn(
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
        return self

    @model_validator(mode="after")
    def assemble_db_async_connection(self) -> t.Self:
        if isinstance(self.ASYNC_DATABASE_ENDPOINT, str):
            return self
        self.ASYNC_DATABASE_ENDPOINT = PostgresDsn(
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
        return self

    START_POSITION: tuple[int, int]
    START_DIRECTION: enums.Direction
    INITIAL_OBSTACLES: tuple[tuple[int, int], ...] | None = None

    IN_CI: bool = False


settings = Settings()
