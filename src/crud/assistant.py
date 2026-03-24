from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import UserModel, DocumentModel
from src.enums import UserGroupEnum
from src.exceptions import DocumentNotFoundError
from src.schemas import AskResponseSchema, AskRequestSchema, AskSummaryResponseSchema, AskSummaryRequestSchema
from src.services import generate_answer, generate_summary


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

async def send_summary_request(
        db: AsyncSession,
        authenticated_user_data: UserModel,
        request_data: AskSummaryRequestSchema
) -> AskSummaryResponseSchema:
    """Crud for ask assistant to make summary of the document."""
    document_id = request_data.document_id
    is_admin = authenticated_user_data.group.name == UserGroupEnum.ADMIN

    if is_admin:
        query = select(DocumentModel.id).where(DocumentModel.id == document_id)
    else:
        query = select(DocumentModel.id).where(
            DocumentModel.id == document_id,
            DocumentModel.users.any(UserModel.id == authenticated_user_data.id)
        )

    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if document is None:
        raise DocumentNotFoundError("Document not found or access denied")

    return await generate_summary(
        document_id=document_id,
        user_id=authenticated_user_data.id,
        is_admin=is_admin
    )
