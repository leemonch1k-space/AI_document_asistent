from typing import Annotated

from fastapi import APIRouter, status, HTTPException
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud import (
    create_new_user,
    login_user,
    refresh_token,
)
from src.config.dependencies import get_jwt_manager, get_db
from src.config.settings import get_settings, Settings
from src.exceptions import (
    BaseUserException,
    IncorrectCredentialsError,
    TokenExpiredError,
    InvalidTokenError,
)
from src.schemas import (
    UserReadSchema,
    UserCreateSchema,
    UserLoginSchema,
    LoginResponseSchema,
    RefreshTokenResponseSchema,
    RefreshTokenSchema,
)
from src.security import JWTAuthManagerInterface


auth_router = APIRouter(prefix="/accounts", tags=["Auth"])


@auth_router.post(
    "/register/",
    status_code=status.HTTP_201_CREATED,
    response_model=UserReadSchema,
    summary="Register a new user",
    description="Create a new user",
)
async def create_account(
    db: Annotated[AsyncSession, Depends(get_db)],
    user_data: UserCreateSchema,
) -> UserReadSchema:
    """Controller for creating new user."""
    try:
        return await create_new_user(
            db=db,
            user_data=user_data,
        )
    except BaseUserException as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


@auth_router.post(
    "/login/",
    status_code=status.HTTP_200_OK,
    response_model=LoginResponseSchema,
    summary="User Login",
    description="Authenticate user and return access and refresh tokens.",
)
async def login(
    db: Annotated[AsyncSession, Depends(get_db)],
    jwt_manager: Annotated[JWTAuthManagerInterface, Depends(get_jwt_manager)],
    settings: Annotated[Settings, Depends(get_settings)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> LoginResponseSchema:
    """Controller for user authentication."""
    user_data = UserLoginSchema(
        login=form_data.username,
        password=form_data.password
    )
    try:
        result = await login_user(
            db=db,
            jwt_manager=jwt_manager,
            settings=settings,
            login_data=user_data,
        )
        return result
    except IncorrectCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


@auth_router.post(
    "/refresh-token/",
    status_code=status.HTTP_200_OK,
    response_model=RefreshTokenResponseSchema,
    summary="Refresh Access Token",
    description="Get a new access token using valid refresh token.",
)
async def refresh_account_token(
    token: RefreshTokenSchema,
    jwt_manager: Annotated[JWTAuthManagerInterface, Depends(get_jwt_manager)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> RefreshTokenResponseSchema:
    """Controller for getting refresh token."""
    try:
        return await refresh_token(
            token=token,
            jwt_manager=jwt_manager,
            settings=settings,
        )
    except (TokenExpiredError, InvalidTokenError, IncorrectCredentialsError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Provided JWT Token incorrect or expired",
        )
