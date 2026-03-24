from enum import StrEnum, auto


class DocumentStatusEnum(StrEnum):
    """Enum class for document status."""
    PROCESSING = auto()
    PROCESSED = auto()
    FAILED = auto()
