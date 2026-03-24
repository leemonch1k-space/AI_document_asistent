from typing import Annotated

from fastapi import APIRouter, status, HTTPException
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud import (
    send_question, send_summary_request
)
from src.config.dependencies import get_db, get_authenticated_user
from src.database.models import UserModel
from src.exceptions import (
    BaseAgentException, DocumentNotFoundError,
)
from src.schemas import AskRequestSchema, AskResponseSchema, AskSummaryRequestSchema, AskSummaryResponseSchema

assistant_router = APIRouter(prefix="/assistant", tags=["AI"])


@assistant_router.post(
    "/ask",
    status_code=status.HTTP_200_OK,
    response_model=AskResponseSchema,
    summary="Ask ai about document",
    description="Make request to AI assistant",
)
async def ask(
        authenticated_user_data: Annotated[
            UserModel, Depends(get_authenticated_user)
        ],
        db: Annotated[AsyncSession, Depends(get_db)],
        question_data: AskRequestSchema
) -> AskResponseSchema:
    """Controller for asking question to AI assistant."""
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

@assistant_router.post(
    "/summary",
    status_code=status.HTTP_200_OK,
    response_model=AskSummaryResponseSchema,
    summary="Ask AI to summarize document",
    description="Make request to AI assistant to get summary of the book",
)
async def ask_summary(
        authenticated_user_data: Annotated[
            UserModel, Depends(get_authenticated_user)
        ],
        db: Annotated[AsyncSession, Depends(get_db)],
        request_data: AskSummaryRequestSchema
) -> AskSummaryResponseSchema:
    """Controller for asking question to AI assistant."""
    try:
        return await send_summary_request(
            db=db,
            authenticated_user_data=authenticated_user_data,
            request_data=request_data
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
