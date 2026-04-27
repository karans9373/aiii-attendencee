from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "WorkPulse AI"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 1440
    database_url: str = "sqlite:///./workpulse.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:19006,http://127.0.0.1:19006"

    @property
    def cors_origins_list(self) -> List[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
