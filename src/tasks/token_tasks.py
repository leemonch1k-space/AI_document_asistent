import asyncio
from src.config.celery_app import celery_instance
from src.database.celery_session import task_db_session
from src.database.models import RefreshTokenModel
from src.services import remove_expired_tokens

# Celery task for tokens


async def _run_cleanup():
    """Support method for celery task."""
    async with task_db_session() as db:
        await remove_expired_tokens(token_type=RefreshTokenModel, db=db)


@celery_instance.task(name="remove_expired_refresh_tokens_task")
def remove_expired_refresh_tokens_task() -> None:
    """
    Remove expired refresh tokens.
    """
    asyncio.run(_run_cleanup())
