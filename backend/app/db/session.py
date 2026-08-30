from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

# SQLite (used in tests / lightweight dev) doesn't support the pool_size /
# max_overflow knobs that real Postgres deployments need.
_engine_kwargs = {"echo": settings.DEBUG, "future": True}
if not settings.DATABASE_URL.startswith("sqlite"):
    _engine_kwargs |= {"pool_size": 10, "max_overflow": 20, "pool_pre_ping": True}

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
