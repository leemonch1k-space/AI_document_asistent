from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import UserModel, DocumentModel
from src.enums import UserGroupEnum
from src.exceptions import DocumentNotFoundError
from src.schemas import AskResponseSchema, AskRequestSchema
from src.services import generate_answer


async def send_question(
        db: AsyncSession,
        authenticated_user_data: UserModel,
        question_data: AskRequestSchema
) -> AskResponseSchema:
    """Crud for validating access and sending question to assistant."""

    is_admin = authenticated_user_data.group.name == UserGroupEnum.ADMIN
    document_ids = question_data.document_ids
    question = question_data.question

    if not document_ids:
        return await generate_answer(
            question=question,
            valid_document_ids=[],
            user_id=authenticated_user_data.id,
            is_admin=is_admin
        )

    if is_admin:
        query = select(DocumentModel.id).where(DocumentModel.id.in_(document_ids))
    else:
        query = select(DocumentModel.id).where(
            DocumentModel.id.in_(document_ids),
            DocumentModel.users.any(UserModel.id == authenticated_user_data.id)
        )

    result = await db.execute(query)
    valid_doc_ids = result.scalars().all()

    if len(valid_doc_ids) != len(document_ids):
        raise DocumentNotFoundError("One or more documents not found or access denied")

    return await generate_answer(
        question=question,
        valid_document_ids=[str(doc_id) for doc_id in valid_doc_ids],
        user_id=authenticated_user_data.id,
        is_admin=is_admin
    )
