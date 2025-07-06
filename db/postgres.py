import sqlalchemy  # noqa
from core.settings import settings
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base


# Создаём базовый класс для будущих моделей
Base = declarative_base()

# Создаём движок
# Настройки подключения к БД передаём из переменных окружения, которые заранее загружены в файл настроек
engine = create_async_engine(settings.pg_dsn.encoded_string(), echo=settings.debug, future=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

if settings.jaeger_trace:
    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


async def create_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def purge_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
