import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from src.config.settings import get_settings


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


async def check_database_connection():
    """Supporting script for database health checking."""
    logger.info("Waiting for database to become ready...")

    engine = create_async_engine(settings.DATABASE_URL)

    max_retries = 15
    retry_interval = 2

    for attempt in range(max_retries):
        try:
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))

            logger.info("Database is fully initialized and ready to accept connections! 🚀")
            await engine.dispose()
            return

        except Exception as e:
            logger.warning(
                f"Database not ready yet... Waiting {retry_interval} seconds. "
                f"(Attempt {attempt + 1}/{max_retries})"
            )
            await asyncio.sleep(retry_interval)

    logger.error("Could not connect to the database after multiple retries.")
    raise ConnectionError("Database connection failed.")


if __name__ == "__main__":
    asyncio.run(check_database_connection())