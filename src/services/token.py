from datetime import datetime, timezone

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from celery.utils.log import get_task_logger

from src.database.models import RefreshTokenModel


logger = get_task_logger(__name__)


async def remove_expired_tokens(
    token_type: type[RefreshTokenModel], db: AsyncSession
) -> None:
    """
    Service for celery task.
    Method for clearing expressed tokens.
    """
    stmt = delete(token_type).where(
        token_type.expires_at < datetime.now(timezone.utc)
    )

    await db.execute(stmt)
    await db.commit()
    logger.info(f"Token '{token_type.token}' deleted successfully.")
