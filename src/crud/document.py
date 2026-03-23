import shutil
import logging
from typing import Annotated
from uuid import uuid4, UUID

from fastapi import UploadFile
from fastapi.params import Depends

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession


from src.config.dependencies import get_db, RAW_STORAGE_DIR
from src.database.models import DocumentModel, UserModel
from src.enums import DocumentStatusEnum, UserGroupEnum
from src.exceptions import UnSupportedFormatError, DocumentNotFoundError
from src.schemas import DocumentResponseSchema, DocumentListResponseSchema
from src.services import delete_document_embedding, delete_document_file
from src.tasks.document_tasks import prepare_document_task


logging.basicConfig(filename='crud.log', level=logging.DEBUG, filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')


async def upload_file(
    authenticated_user_data: UserModel,
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile
) -> DocumentResponseSchema:
    """Crud for uploading new document."""
    allowed_expansion = {"txt", "pdf", "md"}
    file_format = file.filename.split(".")[-1]
    if not (file_format in allowed_expansion):
        raise UnSupportedFormatError("File format unsupported!")

    new_doc = DocumentModel(
        id=uuid4(),
        name=file.filename,
        status=DocumentStatusEnum.PROCESSING,
        chunk_count=0
    )
    current_user = await db.merge(authenticated_user_data)
    new_doc.users.append(current_user)

    db.add(new_doc)
    try:
        await db.commit()
        await db.refresh(new_doc)
    except IntegrityError:
        await db.rollback()
        raise

    file_location = RAW_STORAGE_DIR / f"{new_doc.id}_{file.filename}"
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)

    prepare_document_task.delay(
        str(new_doc.id),
        str(file_location),
        file_format,
        authenticated_user_data.id
    )

    return DocumentResponseSchema(document_id=new_doc.id, status=new_doc.status)


async def get_files(
        authenticated_user_data: UserModel,
        db: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentListResponseSchema:
    """Crud for getting document list."""
    if authenticated_user_data.group.name == UserGroupEnum.ADMIN:
        query = select(DocumentModel)
    else:
        query = select(DocumentModel).where(
            DocumentModel.users.any(UserModel.id == authenticated_user_data.id)
        )

    result = await db.execute(query)
    documents_db = result.scalars().all()

    return DocumentListResponseSchema(documents=documents_db)


async def delete_file(
        authenticated_user_data: UserModel,
        db: Annotated[AsyncSession, Depends(get_db)],
        file_id: UUID
) -> None:
    """Crud for deleting document and its resources."""
    try:
        if authenticated_user_data.group.name == UserGroupEnum.ADMIN:
            query = select(DocumentModel).where(DocumentModel.id == file_id)
        else:
            query = select(DocumentModel).where(
                DocumentModel.id == file_id,
                DocumentModel.users.any(UserModel.id == authenticated_user_data.id)
            )

        result = await db.execute(query)
        document = result.scalar_one()

        file_name = f"{document.id}_{document.name}"

        await delete_document_embedding(file_id)
        await delete_document_file(file_name)

        await db.delete(document)
        await db.commit()

    except NoResultFound:
        raise DocumentNotFoundError("Document not found or access denied")
    except IntegrityError:
        await db.rollback()
        raise
