from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.pool import NullPool

from src.config.settings import get_settings

# celery dependency for getting session for celery

settings = get_settings()


@asynccontextmanager
async def task_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Generate database session for Celery tasks.
    """
    engine = create_async_engine(
        settings.DATABASE_URL,
        poolclass=NullPool,
        echo=False
    )

    session_maker = async_sessionmaker(
        bind=engine, expire_on_commit=False, autoflush=False
    )

    async with session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
            await engine.dispose()
