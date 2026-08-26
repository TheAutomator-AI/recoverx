import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def get_default_database_url() -> str:
    if os.getenv("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    if os.getenv("VERCEL"):
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


settings = Settings()
