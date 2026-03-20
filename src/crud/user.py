from datetime import timedelta
from typing import Annotated

from fastapi.params import Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import (
    UserModel,
    UserGroupModel,
    RefreshTokenModel,
)
from src.enums import (
    UserGroupEnum,
)
from src.exceptions import (
    UserAlreadyExistError,
    UserGroupNotExistError,
    IncorrectCredentialsError,
)
from src.schemas import (
    UserCreateSchema,
    UserReadSchema,
    UserLoginSchema,
    LoginResponseSchema,
    RefreshTokenSchema,
    RefreshTokenResponseSchema,
)
from src.config.settings import get_settings, Settings
from src.config.dependencies import get_jwt_manager, get_db
from src.security import JWTAuthManagerInterface


async def get_user_by_login(
    db: Annotated[AsyncSession, Depends(get_db)],
    login: str,
) -> UserModel | None:
    """support method for getting user instance by user logic."""
    result = await db.execute(
        select(UserModel)
        .where(UserModel.login == login)
        .options(selectinload(UserModel.group))
    )
    user = result.scalar_one_or_none()
    return user


async def create_new_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    user_data: UserCreateSchema,
) -> UserReadSchema:
    """Crud for creating new user."""
    existing_user = await get_user_by_login(db=db, login=user_data.login)

    if existing_user:
        raise UserAlreadyExistError(
            message="User with provided login already exists"
        )

    user_dict = user_data.model_dump()

    group_name = user_dict.pop("group") or UserGroupEnum.USER
    result = await db.execute(
        select(UserGroupModel).where(UserGroupModel.name == group_name)
    )
    user_group = result.scalar_one_or_none()
    if not user_group:
        raise UserGroupNotExistError(message="Provided group does not exist")
    try:
        user = UserModel.create(
            login=user_dict["login"],
            raw_password=user_dict["password"],
            group_id=user_group.id,
        )
        db.add(user)

        await db.commit()
        await db.refresh(user)

    except IntegrityError:
        await db.rollback()
        raise

    return UserReadSchema(id=user.id, login=user.login, permission=group_name)


async def login_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    jwt_manager: Annotated[JWTAuthManagerInterface, Depends(get_jwt_manager)],
    settings: Annotated[Settings, Depends(get_settings)],
    login_data: UserLoginSchema,
) -> LoginResponseSchema:
    """
    Crud for user authentification.
    Compatible with Swagger authorization.
    """
    login = login_data.login
    user = await get_user_by_login(db=db, login=login)
    if not user:
        raise IncorrectCredentialsError(message="Incorrect credentials")

    password = login_data.password
    if not user.check_password(password):
        raise IncorrectCredentialsError(message="Incorrect credentials")

    token_data = {
        "user_id": user.id,
        "login": user.login,
    }
    access_token = jwt_manager.create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=settings.ACCESS_KEY_TIMEDELTA_MINUTES),
    )
    refresh_token = jwt_manager.create_refresh_token(
        data=token_data,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_DAYS),
    )

    db_token = RefreshTokenModel.create(
        token=refresh_token,
        user_id=user.id,
    )
    db.add(db_token)
    await db.commit()

    return LoginResponseSchema(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


async def refresh_token(
    token: RefreshTokenSchema,
    jwt_manager: Annotated[JWTAuthManagerInterface, Depends(get_jwt_manager)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> RefreshTokenResponseSchema:
    """Crud for getting access token using refresh token."""
    payload = jwt_manager.decode_refresh_token(token.refresh_token)

    user_id = payload.get("user_id")
    login = payload.get("login")

    if not user_id or not login:
        raise IncorrectCredentialsError(message="Invalid token credentials")

    new_token = jwt_manager.create_access_token(
        data={
            "user_id": user_id,
            "login": login,
        },
        expires_delta=timedelta(minutes=settings.ACCESS_KEY_TIMEDELTA_MINUTES),
    )

    return RefreshTokenResponseSchema(access_token=new_token)
