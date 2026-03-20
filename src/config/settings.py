import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, computed_field


# Main settings for environment

class BaseAppSettings(BaseSettings):
    """Base settings class."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    BASE_DIR: Path = Path(__file__).parent.parent
    ENVIRONMENT: str = "placeholder_environment"
    API_PREFIX: str = "/api/"

    ACCESS_KEY_TIMEDELTA_MINUTES: int = 60
    REFRESH_TOKEN_DAYS: int = 7

    SECRET_KEY_ACCESS: str = "placeholder_access"
    SECRET_KEY_REFRESH: str = "placeholder_refresh"
    JWT_SIGNING_ALGORITHM: str = "placeholder_algorithm"

    REDIS_HOST: str = "placeholder_rHost"
    REDIS_PORT: int = 0

    QDRANT_HOST: str = "placeholder_qHost"
    QDRANT_PORT: int = 0

    @property
    def DATABASE_URL(self) -> str:
        return "placeholder_algorithm"

    @property
    def QDRANT_URL(self) -> str:
        return "placeholder_qdrant_url"


class DevSettings(BaseAppSettings):
    """DEV_SETTINGS: Local SQLite."""

    ENVIRONMENT: str = "dev"

    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333

    @property
    def DATABASE_URL(self) -> str:
        return "sqlite+aiosqlite:///dev_db"

    @property
    def QDRANT_URL(self) -> str:
        return f"http://{self.QDRANT_HOST}:{self.QDRANT_PORT}"


class Settings(BaseAppSettings):
    """Main settings: postgres."""

    ENVIRONMENT: str = "docker"

    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "admin")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "postgres_db")
    POSTGRES_DB_PORT: int = int(os.getenv("POSTGRES_DB_PORT", 5432))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "auction_db")

    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "qdrant_db")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", 6333))

    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis_db")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))

    SECRET_KEY_ACCESS: str = Field(
        default_factory=lambda: os.getenv(
            "SECRET_KEY_ACCESS",
            os.urandom(32).hex()
        )
    )
    SECRET_KEY_REFRESH: str = Field(
        default_factory=lambda: os.getenv(
            "SECRET_KEY_REFRESH",
            os.urandom(32).hex())
    )
    JWT_SIGNING_ALGORITHM: str = Field(
        default_factory=lambda: os.getenv("JWT_SIGNING_ALGORITHM", "HS256")
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}"
            f":{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}"
            f":{self.POSTGRES_DB_PORT}/{self.POSTGRES_DB}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def QDRANT_URL(self) -> str:
        return f"http://{self.QDRANT_HOST}:{self.QDRANT_PORT}"

def get_settings() -> BaseAppSettings:
    environment = os.environ.get("ENVIRONMENT", "dev")

    if environment == "docker":
        return Settings()
    return DevSettings()
