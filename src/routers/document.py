from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, status, HTTPException, UploadFile
from fastapi.params import Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud import (
    upload_file,
    get_files, delete_file
)
from src.config.dependencies import get_db, get_authenticated_user
from src.database.models import UserModel
from src.exceptions import (
    BaseDocumentException, DocumentNotFoundError,
)
from src.schemas import DocumentResponseSchema, DocumentListResponseSchema

document_router = APIRouter(prefix="/document", tags=["Documents"])


@document_router.post(
    "/documents/",
    status_code=status.HTTP_201_CREATED,
    response_model=DocumentResponseSchema,
    summary="Upload document",
    description="Upload file",
)
async def upload_document(
        authenticated_user_data: Annotated[
            UserModel, Depends(get_authenticated_user)
        ],
        db: Annotated[AsyncSession, Depends(get_db)],
        file: UploadFile
) -> DocumentResponseSchema:
    """Controller for uploading file."""
    try:
        return await upload_file(
            authenticated_user_data=authenticated_user_data,
            db=db,
            file=file
        )
    except BaseDocumentException as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )
    except IntegrityError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error)
        )

@document_router.get(
    "/documents/",
    status_code=status.HTTP_200_OK,
    response_model=DocumentListResponseSchema,
    summary="Get document list",
    description="Shows all uploaded documents",
)
async def get_documents(
        authenticated_user_data: Annotated[
            UserModel, Depends(get_authenticated_user)
        ],
        db: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentListResponseSchema:
    """Controller for getting document list."""
    try:
        return await get_files(
            authenticated_user_data=authenticated_user_data,
            db=db
        )
    except BaseDocumentException as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )

@document_router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete document",
    description="Remove document by id",
)
async def delete_document(
        authenticated_user_data: Annotated[
            UserModel, Depends(get_authenticated_user)
        ],
        db: Annotated[AsyncSession, Depends(get_db)],
        document_id: UUID
) -> None:
    """Controller for getting document list."""
    try:
        return await delete_file(
            authenticated_user_data=authenticated_user_data,
            db=db,
            file_id=document_id
        )
    except DocumentNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )
    except BaseDocumentException as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )
    except IntegrityError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error)
        )
