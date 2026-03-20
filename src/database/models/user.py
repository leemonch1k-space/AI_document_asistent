from datetime import datetime, timezone, timedelta
import uuid
from typing import List

from sqlalchemy import (
    String,
    Integer,
    ForeignKey,
    Enum,
    DateTime,
    func,
    Column, Table,
)
from sqlalchemy.orm import Mapped, relationship, mapped_column

from src.config.settings import get_settings
from src.database import Base
from src.enums import UserGroupEnum, DocumentStatusEnum
from src.security import hash_password, verify_password


settings = get_settings()


user_document_association = Table(
    "user_document",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("document_id", ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True),
)

class UserGroupModel(Base):
    """
    Table model for user's permission group.
    """
    __tablename__ = "user_groups"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    name: Mapped[UserGroupEnum] = mapped_column(
        Enum(UserGroupEnum), nullable=False, unique=True
    )

    users: Mapped[List["UserModel"]] = relationship(
        "UserModel",
        back_populates="group"
    )

    def __repr__(self) -> str:
        return f"<UserGroupModel(id={self.id}, name={self.name})>"


class UserModel(Base):
    """
    Table model for user.
    As simplification, I didn't do a lot for it,
    so it is just a simple model for user.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    login: Mapped[str] = mapped_column(
        String(30), nullable=False, unique=True, index=True
    )
    _hashed_password: Mapped[str] = mapped_column(
        "hashed_password", String(255), nullable=False
    )

    group_id: Mapped[int] = mapped_column(
        ForeignKey("user_groups.id", ondelete="CASCADE"), nullable=False
    )

    documents: Mapped[List["DocumentModel"]] = relationship(
        secondary=user_document_association,
        back_populates="users"
    )

    group: Mapped["UserGroupModel"] = relationship(
        "UserGroupModel", back_populates="users"
    )

    refresh_tokens: Mapped[List["RefreshTokenModel"]] = relationship(
        "RefreshTokenModel",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    @property
    def password(self) -> None:
        raise AttributeError("Password is write-only.")

    @password.setter
    def password(self, password: str) -> None:
        hashed_password = hash_password(password)
        self._hashed_password = hashed_password

    def check_password(self, password: str) -> bool:
        return verify_password(password, self._hashed_password)

    @classmethod
    def create(
        cls, login: str, raw_password: str, group_id: int | Mapped[int]
    ) -> "UserModel":
        """
        This method simplifies the creation of a new user by handling
        password hashing and setting required attributes.
        """
        user = cls(login=login, group_id=group_id)
        user.password = raw_password
        return user

    def has_group(self, group_name: UserGroupEnum) -> bool:
        return self.group.name == group_name

    def __repr__(self) -> str:
        return f"<UserModel(id={self.id}, login={self.login}"


class RefreshTokenModel(Base):
    """Table model for refresh token."""
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token: Mapped[str] = mapped_column(
        String(512),
        unique=True,
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc) + timedelta(days=1),
    )

    user: Mapped[UserModel] = relationship(
        "UserModel",
        back_populates="refresh_tokens"
    )

    @classmethod
    def create(
            cls,
            user_id: int | Mapped[int],
            token: str
    ) -> "RefreshTokenModel":
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_DAYS
        )
        return cls(user_id=user_id, expires_at=expires_at, token=token)

    def __repr__(self) -> str:
        return (
            f"<RefreshTokenModel(id={self.id}, "
            f"token={self.token}, expires_at={self.expires_at})>"
        )


class DocumentModel(Base):
    """Table model for document."""
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(), nullable=False)
    status: Mapped[DocumentStatusEnum] = mapped_column(
        Enum(DocumentStatusEnum),
        nullable=False,
        default=DocumentStatusEnum.PROCESSING
    )
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        default=func.now()
    )

    users: Mapped[List["UserModel"]] = relationship(
        secondary=user_document_association,
        back_populates="documents"
    )