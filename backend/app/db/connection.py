from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

settings = get_settings()

# Railway injects DATABASE_URL as postgresql:// — asyncpg requires postgresql+asyncpg://
_db_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
engine = create_async_engine(_db_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    import app.models.vehicle  # noqa: F401 — ensure models are registered
    import app.models.guide    # noqa: F401
    async with engine.begin() as conn:
        await conn.execute(__import__('sqlalchemy').text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
        # Add warnings column to existing tables that predate it
        await conn.execute(__import__('sqlalchemy').text(
            "ALTER TABLE repair_guides ADD COLUMN IF NOT EXISTS warnings JSON DEFAULT '[]'"
        ))
