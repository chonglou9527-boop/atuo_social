from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "atuo-social"
    debug: bool = False

    database_url: str = "sqlite:///./data/atuo.db"
    data_dir: Path = Path("./data")
    media_dir: Path = Path("./data/media")

    secret_key: str = "change-me-please-32-bytes-minimum-key!!"

    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.data_dir.mkdir(parents=True, exist_ok=True)
    s.media_dir.mkdir(parents=True, exist_ok=True)
    return s
