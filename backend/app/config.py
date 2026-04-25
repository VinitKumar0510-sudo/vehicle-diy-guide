from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    anthropic_api_key: str
    database_url: str = "postgresql+asyncpg://diy:diy@localhost:5432/vehicle_diy"
    redis_url: str = "redis://localhost:6379/0"

    tavily_api_key: str = ""
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "VehicleDIYBot/1.0"
    youtube_api_key: str = ""

    log_level: str = "INFO"
    environment: str = "development"

    claude_model: str = "claude-sonnet-4-6"
    claude_vision_model: str = "claude-sonnet-4-6"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
