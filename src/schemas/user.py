from pydantic import BaseModel, field_validator, ConfigDict

from src.enums import UserGroupEnum
from src.exceptions import IncorrectPasswordError, IncorrectLoginError
from src.validators import (
    validate_password_strength as validate_password,
    validate_login,
)


class UserBaseSchema(BaseModel):
    """Base schema for user."""
    login: str


class UserCreateSchema(UserBaseSchema):
    """Schema for creating user instance."""
    group: UserGroupEnum | None = None
    password: str

    @field_validator("login")
    @classmethod
    def validate_login(cls, v: str) -> str:
        try:
            return validate_login(login=v)
        except ValueError as error:
            raise IncorrectLoginError(str(error))

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        try:
            return validate_password(password=v)
        except ValueError as error:
            raise IncorrectPasswordError(str(error))


class UserReadSchema(UserBaseSchema):
    """Schema for user response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    login: str
    permission: UserGroupEnum | None = None


class UserLoginSchema(BaseModel):
    """Schema for user authentication."""
    login: str
    password: str


class LoginResponseSchema(BaseModel):
    """Schema for authorization response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenSchema(BaseModel):
    """Schema for creating access token."""
    refresh_token: str


class RefreshTokenResponseSchema(BaseModel):
    """Schema for access token response."""
    access_token: str
