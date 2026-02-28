import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str  # 기본값 없음 — .env 필수
    redis_url: str = "redis://localhost:6379/0"
    app_title: str = "TechDeal-Hub API"
    app_version: str = "1.0.0"
    debug: bool = False
    allowed_origins: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()
