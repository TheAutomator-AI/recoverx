import os
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def get_default_database_url() -> str:
    env_db = os.getenv("DATABASE_URL")
    if env_db and env_db.strip():
        return env_db.strip()
    if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        return "sqlite:////tmp/recoverx.db"
    db_file = PROJECT_ROOT / "recoverx.db"
    return f"sqlite:///{db_file.as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "RecoverX — AI Revenue Recovery API"
    app_version: str = "1.0.0"
    database_url: str = get_default_database_url()
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "*",
    ]
    random_seed: int = 42

    @field_validator("app_name", mode="before")
    @classmethod
    def parse_app_name(cls, v):
        if not v or not str(v).strip():
            return "RecoverX — AI Revenue Recovery API"
        return str(v).strip()

    @field_validator("app_version", mode="before")
    @classmethod
    def parse_app_version(cls, v):
        if not v or not str(v).strip():
            return "1.0.0"
        return str(v).strip()

    @field_validator("random_seed", mode="before")
    @classmethod
    def parse_random_seed(cls, v):
        if v is None or v == "":
            return 42
        try:
            return int(v)
        except (ValueError, TypeError):
            return 42

    @field_validator("database_url", mode="before")
    @classmethod
    def parse_database_url(cls, v):
        if not v or not str(v).strip():
            return get_default_database_url()
        return str(v).strip()


settings = Settings()
