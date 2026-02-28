from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://techdeal:changeme@localhost:5432/techdeal"
    redis_url: str = "redis://localhost:6379/0"
    app_title: str = "TechDeal-Hub API"
    app_version: str = "1.0.0"

    class Config:
        env_file = ".env"


settings = Settings()
