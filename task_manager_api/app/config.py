import warnings
from typing import List

from pydantic import model_validator
from pydantic_settings import BaseSettings

_INSECURE_DEFAULT_KEY = "changeme-secret-key-for-dev"


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/taskmanager"
    SECRET_KEY: str = _INSECURE_DEFAULT_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    TEST_DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/taskmanager_test"
    ALLOWED_ORIGINS: List[str] = ["*"]

    model_config = {"env_file": ".env", "extra": "ignore"}

    @model_validator(mode="after")
    def warn_insecure_defaults(self) -> "Settings":
        if self.SECRET_KEY == _INSECURE_DEFAULT_KEY:
            warnings.warn(
                "SECRET_KEY is set to the insecure default value. "
                "Set SECRET_KEY in your environment before deploying.",
                stacklevel=2,
            )
        return self


settings = Settings()
