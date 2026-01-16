from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "project_80"
    app_timezone: str = "Asia/Shanghai"

    app_basic_auth_user: str | None = "wangjian"
    app_basic_auth_pass: str | None = "jian4643911"

    user_height_cm: float = 170.0
    goal_weight_kg: float = 80.0

    database_url: str

    upload_dir: Path = Path("storage/uploads")
    max_upload_mb: int = 10


settings = Settings()

