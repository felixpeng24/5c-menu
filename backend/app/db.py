from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlmodel import SQLModel, select

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


_HALL_SEEDS = [
    {"id": "hoch", "name": "Hoch-Shanahan", "college": "HMC", "vendor_type": "sodexo", "color": "#000000"},
    {"id": "collins", "name": "Collins", "college": "CMC", "vendor_type": "bonappetit", "color": "#8B0000"},
    {"id": "malott", "name": "Malott", "college": "Scripps", "vendor_type": "bonappetit", "color": "#2E5339"},
    {"id": "mcconnell", "name": "McConnell", "college": "Pitzer", "vendor_type": "bonappetit", "color": "#F47920"},
    {"id": "frank", "name": "Frank", "college": "Pomona", "vendor_type": "pomona", "color": "#004B8D"},
    {"id": "frary", "name": "Frary", "college": "Pomona", "vendor_type": "pomona", "color": "#004B8D"},
    {"id": "oldenborg", "name": "Oldenborg", "college": "Pomona", "vendor_type": "pomona", "color": "#004B8D"},
]


async def init_db() -> None:
    """Create all tables and seed dining halls if empty."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    from app.models.dining_hall import DiningHall

    async with async_session_factory() as session:
        result = await session.execute(select(DiningHall).limit(1))
        if result.scalars().first() is None:
            for seed in _HALL_SEEDS:
                session.add(DiningHall(**seed))
            await session.commit()
