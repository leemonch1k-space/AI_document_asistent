class BaseDocumentException(Exception):
    """Base document exception class."""
    def __init__(self, message: str | None = None) -> None:
        if message is None:
            message = "Something went wrong during document operation"
        super().__init__(message)


class UnSupportedFormatError(BaseDocumentException):
    """Exception raised when user upload file with unsupported expansion."""
    pass

class DocumentNotFoundError(BaseDocumentException):
    """Exception raised when user interacts with file which not exists."""
    pass