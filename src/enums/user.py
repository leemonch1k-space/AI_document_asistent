from enum import StrEnum, auto


class UserGroupEnum(StrEnum):
    """Enum class for user permission groups."""
    USER = auto()
    ADMIN = auto()
