class BaseAgentException(Exception):
    """Base document exception class."""
    def __init__(self, message: str | None = None) -> None:
        if message is None:
            message = "Something went wrong during document operation"
        super().__init__(message)
