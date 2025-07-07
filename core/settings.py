from datetime import timedelta
from logging import config as logging_config

from async_fastapi_jwt_auth import AuthJWT
from core.logger import LOGGING
from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings


# Применяем настройки логирования
logging_config.dictConfig(LOGGING)


class PostgresSettings(BaseSettings):
    """Настройки Postgres."""

    echo_database: bool = False
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str

    @property
    def pg_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}"
            f":{self.postgres_password}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )


class Settings(PostgresSettings):
    # Общие настройки
    project_name: str = "Order Service"
    debug: bool = False

    # Настройки Redis
    redis_host: str = "127.0.0.1"
    redis_port: int = 6379

    # Настройки AuthJWT
    authjwt_secret_key: str = "secret"

    # Настройка телеметрии
    jaeger_trace: bool = True
    jaeger_agent_host: str = "localhost"
    jaeger_agent_port: int = 6831


@AuthJWT.load_config
def get_config():
    return Settings()


settings = Settings()
