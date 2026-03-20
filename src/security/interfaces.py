from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Optional


class JWTAuthManagerInterface(ABC):
    """
    Interface for JWT Authentication Manager.
    """

    @abstractmethod
    def create_access_token(
        self,
        data: dict[str, object],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create a new access token.
        """
        pass

    @abstractmethod
    def create_refresh_token(
        self,
        data: dict[str, object],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create a new refresh token.
        """
        pass

    @abstractmethod
    def decode_access_token(self, token: str) -> dict[str, object]:
        """
        Decode and validate an access token.
        """
        pass

    @abstractmethod
    def decode_refresh_token(self, token: str) -> dict[str, object]:
        """
        Decode and validate a refresh token.
        """
        pass

    @abstractmethod
    def verify_refresh_token_or_raise(self, token: str) -> None:
        """
        Verify a refresh token or raise an error if invalid.
        """
        pass

    @abstractmethod
    def verify_access_token_or_raise(self, token: str) -> None:
        """
        Verify an access token or raise an error if invalid.
        """
        pass
