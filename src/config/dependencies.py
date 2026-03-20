from pathlib import Path
from typing import Any, AsyncGenerator, Annotated

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette import status

from src.config.settings import BaseAppSettings, get_settings
from src.database.engine import AsyncSessionLocal
from src.database.models import UserModel
from src.exceptions import TokenExpiredError, InvalidTokenError
from src.security import JWTAuthManagerInterface, JWTAuthManager

# Dependencies

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/accounts/login/")

BASE_DIR = Path(__file__).resolve().parents[2]
STORAGE_DIR = BASE_DIR / "storage"
RAW_STORAGE_DIR = STORAGE_DIR / "raw"
PROCESSED_STORAGE_DIR = STORAGE_DIR / "processed"
FAILED_STORAGE_DIR = STORAGE_DIR / "failed"


async def get_db() -> AsyncGenerator[AsyncSession, Any]:
    """Dependency for getting async db session"""
    async with AsyncSessionLocal() as session:
        yield session


def get_jwt_manager(
    settings: Annotated[BaseAppSettings, Depends(get_settings)],
) -> JWTAuthManagerInterface:
    """Dependency for getting jwt manager."""
    return JWTAuthManager(
        secret_key_access=settings.SECRET_KEY_ACCESS,
        secret_key_refresh=settings.SECRET_KEY_REFRESH,
        algorithm=settings.JWT_SIGNING_ALGORITHM,
    )


async def get_authenticated_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str, Depends(oauth2_scheme)],
    jwt_manager: Annotated[JWTAuthManagerInterface, Depends(get_jwt_manager)],
) -> type[UserModel] | None:
    """Dependency for getting authenticated user instance."""
    try:
        user_data = jwt_manager.decode_access_token(token)
    except (TokenExpiredError, InvalidTokenError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Invalid or expired"
        )

    user_id = user_data.get("user_id")

    return await db.get(
        UserModel,
        user_id,
        options=[
            joinedload(UserModel.group),
            joinedload(UserModel.collection)
        ],
    )