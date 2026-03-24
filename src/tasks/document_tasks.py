import asyncio

from celery.utils.log import get_task_logger

from src.config.celery_app import celery_instance
from src.database.celery_session import task_db_session
from src.services import prepare_document

# Celery task for documents


logger = get_task_logger(__name__)


async def _run_document_preparation(
        document_id: str,
        file_location: str,
        file_format: str,
        user_id: int
):
    """Support method for celery task."""
    async with task_db_session() as db:
        await prepare_document(
            document_id=document_id,
            file_location=file_location,
            db=db,
            file_format=file_format,
            user_id=user_id
        )

@celery_instance.task(name="prepare_document_task")
def prepare_document_task(
        document_id: str,
        file_location: str,
        file_format: str,
        user_id: int
) -> None:
    """Prepare document."""
    logger.info(f"TASK 'prepare document' started on document {document_id}")
    asyncio.run(_run_document_preparation(
        document_id=document_id,
        file_location=file_location,
        file_format=file_format,
        user_id=user_id
    ))
