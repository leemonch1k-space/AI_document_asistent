from enum import StrEnum, auto


class DocumentStatusEnum(StrEnum):
    PROCESSING = auto()
    PROCESSED = auto()
    FAILED = auto()
