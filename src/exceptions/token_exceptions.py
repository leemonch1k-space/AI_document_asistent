class BaseTokenException(Exception):
    """Base token exception class."""
    def __init__(self, message: str | None = None) -> None:
        if message is None:
            message = "Something went wrong during Token operation"
        super().__init__(message)


class TokenExpiredError(BaseTokenException):
    """Exception raised when a token is expired."""
    pass


class InvalidTokenError(BaseTokenException):
    """Exception raised when a token is invalid."""
    pass
