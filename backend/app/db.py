from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlmodel import SQLModel

from app.config import get_settings


def get_engine():
    """Create async SQLAlchemy engine from settings."""
    settings = get_settings()
    return create_async_engine(settings.database_url, echo=False)


engine = get_engine()

async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session for dependency injection."""
    async with async_session_factory() as session:
        yield session


async def init_db() -> None:
    """Create all tables. For dev/test use only."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
