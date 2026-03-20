class BaseUserException(Exception):
    """Base user exception class."""
    def __init__(self, message: str | None = None) -> None:
        if message is None:
            message = "Something went wrong during user operation"
        super().__init__(message)


class IncorrectPasswordError(BaseUserException):
    """Exception raised when user sent incorrect password."""
    pass


class IncorrectLoginError(BaseUserException):
    """Exception raised when user sent incorrect login."""
    pass


class UserAlreadyExistError(BaseUserException):
    """Exception raised when user tries register already taken login."""
    pass


class UserNotExistError(BaseUserException):
    """Exception raised when user not exists."""
    pass


class UserGroupNotExistError(BaseUserException):
    """Exception raised when user group not exists."""
    pass


class IncorrectCredentialsError(BaseUserException):
    """Exception raised when user incorrect credentials."""
    pass


class UserPermissionDeniedError(BaseUserException):
    """Exception raised when user not have enough permissions."""
    pass


class InsufficientBalanceError(BaseUserException):
    """Exception raised when user not have enough balance."""
    pass
