from typing import Annotated

from fastapi import APIRouter, status, HTTPException
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud import (
    send_question
)
from src.config.dependencies import get_db, get_authenticated_user
from src.database.models import UserModel
from src.exceptions import (
    BaseAgentException, DocumentNotFoundError,
)
from src.schemas import AskRequestSchema, AskResponseSchema

assistant_router = APIRouter(prefix="/assistant", tags=["AI"])


@assistant_router.post(
    "/ask",
    status_code=status.HTTP_200_OK,
    response_model=AskResponseSchema,
    summary="Upload document",
    description="Upload document",
)
async def ask(
        authenticated_user_data: Annotated[
            UserModel, Depends(get_authenticated_user)
        ],
        db: Annotated[AsyncSession, Depends(get_db)],
        question_data: AskRequestSchema
) -> AskResponseSchema:
    """Controller for uploading file."""
    try:
        return await send_question(
            db=db,
            authenticated_user_data=authenticated_user_data,
            question_data=question_data
        )
    except DocumentNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )
    except BaseAgentException as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )

